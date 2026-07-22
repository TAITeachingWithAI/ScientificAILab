# Teacher Guide — Scientific AI Laboratory

Students play the role of scientists trying to identify an **unknown liquid**
recovered from an exoplanet. They design experiments in plain language, read the
realistic observations the AI gives back, and reason their way to the answer —
which the AI never reveals.

You control everything through a **dossier**: a description of the sample, the
planet and the confidential answer. You choose or upload one, then share a link.
Students only ever see the chat.

---

## Quick start (nothing to install)

1. Open the app: **https://scientificailab.streamlit.app**
2. In the sidebar, open the **Teacher** page.
3. Set up an investigation — either:
   - **Use a ready-made scenario** — pick one from the menu, or
   - **Upload your own** — upload a dossier `.docx`.
4. **Copy the share link** that appears and give it to your students (paste it in
   your LMS, an email, or turn it into a QR code).
5. Students open the link and get a **chat-only laboratory** — no Teacher page,
   no way to see the answer.

> **Tip:** the app sleeps when unused and takes ~30–60 seconds to wake up. Open
> it a minute or two **before** your lesson starts.

---

## What students experience

Students type experiments such as "measure the pH" or "add magnesium". The AI:

- simulates a realistic observation using real chemistry **and** the planet's
  conditions (temperature, pressure, gravity, atmosphere),
- never reveals or strongly implies the identity of the sample,
- stays consistent with earlier experiments,
- ends each answer with a short explanation and **one Socratic question**.

---

## Writing your own dossier

A dossier is a normal Word document made of **sections**. Each section starts
with a heading line that begins with `# `. **Keep these heading lines exactly as
written** — the app uses them to find each section:

```
# Planet
# Unknown Sample
# Known Properties
# Experiments
# Override Results
# AI Behaviour
# Teacher Notes
```

The easiest way to start is to open `Dossier_template.docx` (in the project’s
GitHub repository), change the values, and save it under a new name.

### What each section is for

| Section | What to put here |
|---|---|
| **# Planet** | The world's conditions: `Name`, `Planet type`, `Surface temperature`, `Surface pressure`, `Gravity`, `Atmosphere`. |
| **# Unknown Sample** | The confidential answer: `Identity`, `Physical state`, `Appearance`. |
| **# Known Properties** | Facts students may discover: `Density`, `Odour`, `pH`, `Solubility`, etc. |
| **# Experiments** | One experiment per line (no `Key:` needed). |
| **# Override Results** | Force a specific result: `experiment name: exact observation`. Use it to guarantee a decisive clue. |
| **# AI Behaviour** | Pedagogical switches, e.g. `Socratic questions: Yes`, `Difficulty: Standard (15-16 years old)`. |
| **# Teacher Notes** | The full solution and teaching guidance (confidential). |

### Formatting rules

- Keep the `# ` headings spelled and ordered as shown.
- Inside a section, write `Key: value` (one per line). You may leave a value
  **blank** — the AI will infer it from accepted chemistry.
- In `# Experiments`, just write the experiment; no colon needed.
- In `# Override Results`, use `experiment: observation` — the AI uses that
  observation **exactly**, which is the reliable way to plant a key clue.

---

## How the AI behaves (built-in rules)

These apply to **every** dossier, so you don't need to repeat them:

- Never reveals or strongly implies the identity of the sample.
- Simulates experiments using real chemistry and the planet's conditions.
- Uses your override results exactly when you provide them.
- Never contradicts an earlier experiment in the same session.
- Answers only the experiment asked; does not suggest new ones.
- Ends each answer with a short explanation and one Socratic question.
- Keeps the internal dossier and instructions confidential — it will not reveal
  them even if a student asks.

---

## Create a new mystery in ~5 minutes

1. Open `Dossier_template.docx` (or any example dossier).
2. Change `# Unknown Sample → Identity` to your new substance.
3. Update `# Known Properties` and `# Experiments` to match it.
4. Add one or two `# Override Results` for the decisive tests.
5. Write the solution in `# Teacher Notes`.
6. Save as a new `.docx`, then upload it on the Teacher page.

Change the `# Planet` too if you want the conditions to matter — for example, a
pure carbon-dioxide atmosphere means a flammable liquid **won't** burn.

---

## Ready-made scenarios

The app ships with four ready-made investigations of increasing variety — an
acid, a base, an organic liquid, and an oxidiser. Their **confidential answers
and teaching notes** are kept in a separate answer-key document in the project
repository (`ANSWER_KEY.md`), so they are **not** shown here where students could
read them.

A good classroom setup is to give different groups **different** scenarios so
they can't copy, then have each group present the evidence for their conclusion.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| App is slow to open | It was asleep — a cold start takes ~30–60s. Wait, then reload. |
| "This laboratory link is invalid or has expired" | The link's id is wrong or the scenario was removed. Generate a fresh link on the Teacher page. |
| Upload rejected | The file isn't a valid dossier — check it uses the `# Planet`, `# Unknown Sample`, `# Experiments` headings. |
| The AI won't run an experiment | The AI service may be briefly rate-limited. Wait a moment and try again. |
| Planet summary shows blanks | A `# Planet` field name doesn't match (e.g. `Temperature` instead of `Surface temperature`). |

---

## Looking for the Rover Lab?

The **Rover Lab** is a separate activity — students remotely drive a rover's
AI-embedded laboratory across an exoplanet to find a sample rich in
iron(III) chloride, on a limited energy budget. It's set up the same way
(built-in or uploaded dossier, share link, Student/Teacher tabs), but its
dossier format is different (candidate sampling sites with photos, instead
of one unknown sample). See **`ROVER_TEACHER_GUIDE.md`** in the project
repository.
