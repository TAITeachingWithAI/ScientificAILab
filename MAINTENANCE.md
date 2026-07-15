# Maintenance & Handover Runbook

Practical notes for keeping the **Scientific AI Laboratory** running, coming
back to it after a break, or handing it to someone else.

> ⚠️ This file is in a public repository. **Never put API keys or secrets here.**
> All secrets live in the accounts below and in the team **Bitwarden** vault.

---

## 1. What the app is made of

| Piece | Service | Notes |
|---|---|---|
| Web app hosting | **Streamlit Community Cloud** | https://scientificailab.streamlit.app — deploys automatically from the repo. |
| Source code | **GitHub** | `github.com/TAITeachingWithAI/ScientificAILab`, branch `main`. |
| AI model | **Groq** (free tier) | One shared API key, held in the app's secrets. Model: `llama-3.3-70b-versatile`, fallback `llama-3.1-8b-instant`. |
| Uploaded-scenario storage | **Supabase** (free tier) | S3-compatible bucket `scenarios`. Built-in scenarios do NOT use this — they live in the repo. |
| Secrets store (for humans) | **Bitwarden** | Groq key, Supabase S3 keys, account logins. |

**Where the running app gets its settings:** the Streamlit **Secrets** panel
(Manage app → Settings → Secrets), *not* the `.env` file. The `.env` file is for
local development only and is git-ignored.

---

## 2. Coming back after a break — the 5-minute checklist

Free services go dormant when unused. Do these in order:

1. **Wake / reboot the app.** Open https://scientificailab.streamlit.app. If it's
   asleep it wakes in ~30–60s. If Streamlit deactivated it for inactivity, log in
   at https://share.streamlit.io and **reboot** it from the dashboard.
2. **Un-pause Supabase.** Log in at https://supabase.com. If the project is
   **paused**, click to resume it. (Until you do, *uploaded* scenario links fail;
   built-in scenarios still work.)
3. **Run one test experiment.** Teacher page → pick a built-in scenario → open the
   link → run "measure the pH". If you get a real answer, the AI + Groq key are fine.
4. **If the AI errors**, a Groq model was probably retired — see §4.
5. **Test an upload.** Teacher → Upload your own → upload `Dossier_template.docx` →
   open the link. If it loads, Supabase is working.

If all five pass, you're fully back.

---

## 3. Normal update workflow

Edit locally → test → push. The live app redeploys itself from `main`.

```
cd ScientificAILab
pip install -r requirements.txt          # first time / after dep changes
# copy .env.example to .env and fill in keys for local testing
python -m streamlit run app.py           # test locally
git add -A && git commit -m "..." && git push
```

A push to `main` auto-redeploys within ~a minute. **Test locally before pushing —
a broken push breaks the live app until fixed.**

---

## 4. If the AI stops responding (model retired)

Groq occasionally renames or retires models. Check the current list at
https://console.groq.com/docs/models, then update **either**:

- the Streamlit **Secrets** (for the live app), or
- `.env` (for local), or
- the defaults in `modules/llm.py`.

Relevant settings (all optional — code has defaults):

```
LAB_MODEL=<a current Groq model id>       # primary
LAB_FALLBACKS=groq:<another current id>   # tried if the primary is rate-limited
```

Prefer plain **instruct** models. Avoid *reasoning* models (e.g. `gpt-oss`,
`qwen3`) — testing showed they leak the sample identity or dump their reasoning.

---

## 5. If a key is lost or needs rotating

Keys live in the Streamlit **Secrets** panel and in **Bitwarden**.

- **Groq key:** regenerate at https://console.groq.com/keys → update `GROQ_API_KEY`
  in Streamlit Secrets → the app reboots automatically → update Bitwarden.
- **Supabase S3 keys:** Supabase → Project Settings → Storage → S3 Connection →
  new access key → update `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` in Streamlit
  Secrets and Bitwarden.
- The full set of secret keys the app expects is documented in `.env.example`.

---

## 6. Configurable knobs (in Secrets or `.env`)

| Setting | Default | Purpose |
|---|---|---|
| `LAB_PROVIDER` | `groq` | Which AI provider to use. |
| `LAB_MODEL` | (provider default) | Override the primary model. |
| `LAB_FALLBACKS` | `groq:llama-3.1-8b-instant` | Models tried if the primary fails/rate-limits. |
| `LAB_MAX_TOKENS` | `700` | Max length of each AI reply (protects the token budget). |
| `LAB_HISTORY_TURNS` | `6` | How many past experiments are resent per request. |
| `STORE_BACKEND` | `s3` | `s3` (Supabase) or `local` (dev only). |
| `APP_BASE_URL` | localhost | Must equal the deployed URL so share links are correct. |

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| App won't load at all | Streamlit slept/deactivated | Reboot from share.streamlit.io |
| "invalid or expired" on an uploaded link | Supabase paused | Un-pause the Supabase project |
| Built-in scenarios work, uploads don't | Supabase paused or S3 key changed | Un-pause; check `S3_*` secrets |
| Every experiment errors | Groq model retired, or key revoked | Update `LAB_MODEL`/`LAB_FALLBACKS` (§4); check `GROQ_API_KEY` |
| "try again shortly" / rate-limit | Free daily/minute cap hit (shared key) | Wait; consider adding a Cerebras/OpenRouter key to `LAB_FALLBACKS` |
| App broke after a rebuild with no code change | A dependency shipped a breaking change | `requirements.txt` is pinned to prevent this; if it still happens, check which package changed |
| Share links point to the wrong URL | `APP_BASE_URL` doesn't match the deployed URL | Update `APP_BASE_URL` in Secrets |

---

## 8. Known limitations (by design, not bugs)

- **No login/auth.** A determined student could reach the Teacher page. Keep the
  confidential answer key (`ANSWER_KEY.md`) in mind — it's in this public repo.
- **One shared free key** — everyone shares its daily limit. Fine for classroom
  use; a very popular public launch could hit the cap (see the rate-limit row above).
- **Uploaded scenarios never expire** — they accumulate in Supabase. Harmless for
  a long time; clean out old ones occasionally if you like.
