# Teacher Guide — Scientific AI Laboratory

This guide explains how the laboratory works, how to write your own "mystery
sample" dossiers, and what ready-made scenarios are included.

---

## 1. What the activity is

Students play the role of scientists trying to identify an **unknown liquid**
recovered from an exoplanet. They cannot see the answer. Instead, they:

1. design experiments in plain language ("measure the pH", "add magnesium"),
2. read the realistic observation the AI gives back,
3. reason their way toward the identity.

You, the teacher, control everything through a single **dossier** — a Word
(`.docx`) file that describes the sample, the planet, the allowed experiments
and the confidential answer. You upload it once; students never see it.

---

## 2. How to run it (quick reference)

Detailed setup is in the `README.md`. In short:

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add an API key (a free **Groq** key works
   well — https://console.groq.com/keys).
3. `streamlit run app.py` (or `python -m streamlit run app.py`).
4. In the browser: **Teacher** page → upload a dossier; then **Student** page in
   the same browser tab → run experiments.

> **Tip:** upload the dossier as *Teacher* first, then switch to *Student* in the
> **same browser tab**. In this version the dossier lives in the browser session,
> so a separate tab or a different computer will not see it yet.

---

## 3. The dossier format

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

Inside most sections you write one item per line in the form **`Key: value`**.
Anything you type *above* the first `# ` heading is ignored by the app, so that
is a safe place for your own notes.

### What each section is for

| Section | What to put here | Seen by the AI? |
|---|---|---|
| **# Planet** | The world's conditions: `Name`, `Planet type`, `Surface temperature`, `Surface pressure`, `Gravity`, `Atmosphere`. The AI takes these into account (e.g. no combustion without oxygen). | Yes |
| **# Unknown Sample** | The **confidential answer** — `Identity`, `Physical state`, `Appearance`. The AI knows it but must never reveal it. | Yes (hidden from students) |
| **# Known Properties** | Facts students are allowed to discover: `Density`, `Odour`, `pH`, `Solubility`, etc. | Yes |
| **# Experiments** | One experiment per line (no `Key:` needed). These are the experiments you expect students to try. | Yes |
| **# Override Results** | Force a specific result for a given experiment: `experiment name: exact observation`. Use this to guarantee a key clue. | Yes |
| **# AI Behaviour** | Pedagogical switches: e.g. `Socratic questions: Yes`, `Difficulty: Standard (15-16 years old)`. | Yes |
| **# Teacher Notes** | The full solution and teaching guidance. Confidential. | Yes (hidden from students) |

### Formatting rules

- Keep `# ` headings **spelled and ordered as shown**.
- Use `Key: value` lines (one per line). You may leave a value **blank** — the AI
  will infer it from accepted chemistry rather than treat it as important.
- In `# Experiments`, just write the experiment; no colon needed.
- `# Override Results` uses `experiment: observation`. The AI will use that
  observation **exactly**, which is the reliable way to plant a decisive clue.

---

## 4. How the AI behaves (built-in rules)

These rules live in `modules/prompts.py` and apply to **every** dossier, so you
do not need to repeat them:

- Never reveals or strongly implies the identity of the sample.
- Simulates experiments using real chemistry and the planet's conditions.
- Uses your **override results** exactly when you provide them.
- Never contradicts an earlier experiment in the same session.
- Answers only the experiment asked; does not suggest new ones.
- Ends each answer with a short explanation **and one Socratic question**.
- Uses language suitable for ~15–16 year-olds without dumbing down the science.

If you want to change this pedagogy for the whole platform, edit that one file.

---

## 5. Create a new mystery in ~5 minutes

1. Open `Dossier_template.docx` (or any example dossier).
2. Change `# Unknown Sample → Identity` to your new substance.
3. Update `# Known Properties` and `# Experiments` to match it.
4. Add one or two `# Override Results` for the decisive tests.
5. Write the solution in `# Teacher Notes`.
6. Save as a new file (e.g. `Dossier_Exoplanet_E.docx`) and upload it.

Change the `# Planet` too if you want the conditions to matter — for example, a
pure carbon-dioxide atmosphere means a flammable liquid **won't** burn, which
makes for a good reasoning challenge.

---

## 6. Ready-made scenarios (answer key — keep confidential)

The project ships with four worked examples of increasing variety. Filenames are
neutral on purpose so students can't guess from your screen.

| File | Sample (answer) | Chemistry focus | Level |
|---|---|---|---|
| `Dossier_template.docx` | Hydrochloric acid | Acids, chloride test, reaction with a metal | Standard |
| `example_dossiers/Dossier_Exoplanet_B.docx` | Sodium hydroxide solution | Strong bases, neutralisation, precipitation | Standard |
| `example_dossiers/Dossier_Exoplanet_C.docx` | Ethanol | Physical properties, volatility, combustion | Standard |
| `example_dossiers/Dossier_Exoplanet_D.docx` | Hydrogen peroxide solution | Catalysis, decomposition, the oxygen test | Challenging |

### Suggested learning goals

- **Acid (template):** low pH, effervescence with magnesium (hydrogen gas), and a
  white silver-chloride precipitate with silver nitrate that confirms chloride.
- **Base (B):** very high pH, soapy feel, reaction with aluminium, exothermic
  neutralisation, and a blue copper-hydroxide precipitate. Great as a contrast to
  the acid.
- **Ethanol (C):** low density, neutral pH, evaporates without residue, mixes with
  water, burns with a clean pale-blue flame. Links combustion to the presence of
  oxygen in the atmosphere.
- **Hydrogen peroxide (D):** slightly acidic; decomposes with a catalyst
  (manganese dioxide, or catalase in potato/liver) to release oxygen that
  relights a glowing splint. Introduces catalysts and decomposition reactions.

A good classroom sequence is to give different groups **different** dossiers so
they can't copy answers, then have each group present the evidence that led to
their conclusion.

---

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "The teacher has not uploaded a dossier yet." | Upload as *Teacher* first, and use the **same browser tab** for *Student*. |
| "not configured yet" / "valid API key" error | The `.env` key is missing or wrong. Check `LAB_PROVIDER` matches the key you filled in. |
| Changed `.env` but nothing changed | **Restart** the app (`Ctrl+C`, then run again). The `.env` is read only at startup. |
| "quota exceeded" (429) | The provider's free limit was hit. Wait a moment, use a different key, or switch provider in `.env`. |
| Planet summary shows blanks | A `# Planet` field name doesn't match (e.g. `Temperature` instead of `Surface temperature`). |

---

## 8. Cost

Running the app is free. Each AI response costs a small amount of usage on your
chosen provider; on a **free tier** (Groq / Gemini personal account) a whole
class typically stays within the free limits. For strict privacy or zero ongoing
cost, a local model (via Ollama) can be plugged in later without changing the
Teacher or Student pages.
