# Teacher Guide — Rover Lab

Students play the role of scientists remotely operating a rover on an
exoplanet. Contaminated water has been found there, and purifying it needs
Fe(OH)3 — so mission control needs a sample rich in iron, ideally iron(III)
chloride. Students pick a candidate sampling site from the rover's photos,
then task its onboard AI laboratory with physical tests (pH, density,
conductivity, magnetism, colour reactions…) to work out which site is most
promising — on a limited energy budget, so tests have to be chosen wisely.
The AI never states the answer outright.

You control everything through a **dossier**: the planet, the mission
framing, the rover's energy budget, and each candidate site (its photo,
description, confidential identity, and test results). You choose or upload
one, then share a link. Students only ever see the mission.

**Important design point:** the AI is never told a site's true identity,
even internally — it only ever sees the properties and test results you
write. This is deliberate, and mirrors a real instrument: it can report a
measurement, or reason about what substances would be *consistent* with a
pattern of measurements, but it cannot state a confirmed answer because it
genuinely doesn't have one to leak. This is why the wording of your
`## Experiment Results` matters so much — see below.

---

## Quick start (nothing to install)

1. Open the app: **https://scientificailab.streamlit.app**
2. In the sidebar, open the **Rover Lab** page.
3. Set up a mission — either:
   - **Use a ready-made scenario** — pick one from the menu, or
   - **Upload your own** — upload a rover dossier `.docx`.
4. **Copy the share link** that appears and give it to your students.
5. Students open the link and get a **mission-only view** — no Teacher page,
   no way to see which site is correct.

> **Tip:** the app sleeps when unused and takes ~30–60 seconds to wake up. Open
> it a minute or two **before** your lesson starts.

---

## What students experience

Students see a wide shot of the landing area and a list of candidate sites.
Picking a site (costs energy) shows its close-up photo and description; from
there they can run a physical test from the available-tests list (also costs
energy) or ask the AI lab a general chemistry/geology question at any time,
free of charge. The AI behaves differently depending on which of these two
things a student did:

- **Running a test** gets a short, instrument-style reply — just the
  measured result (e.g. "pH: 1.8 — strongly acidic."), nothing else. Real
  instruments don't editorialise, and this also keeps students turning to
  their own reasoning rather than reading an explanation off the screen.
- **Asking a question** (general chemistry/geology, or "what could this
  site's results mean?") gets a fuller, explanatory answer. When asked what
  a visited site's results could mean, the AI may name a few real substances
  consistent with the pattern of evidence — as possibilities, never a
  conclusion — which is what nudges students toward the answer without
  handing it to them.

Throughout, the AI:

- never states, as fact, what a site "is" or "contains",
- stays consistent with earlier tests,
- narrows down candidates as evidence accumulates, but never gives a
  100%-certain verdict,
- won't suggest what to test next — that decision is left to the student
  (this is enforced by both the prompt and a mechanical filter on the reply,
  so it holds even if the underlying AI model doesn't follow instructions
  perfectly).

There is no "submit your final answer" button — like the Chemistry Lab, the
investigation is meant to end in a class discussion where groups present
their evidence, checked against your `# Teacher Notes`.

---

## Writing your own dossier

A rover dossier is a normal Word document made of **sections**, each starting
with a heading line beginning with `# ` (and, inside a site, `## ` for two
sub-lists). **Keep these heading lines exactly as written**:

```
# Planet
# Mission Briefing
# Rover
# Overview Image
# Site: <a neutral visual description>      (repeat this heading for each site)
## Known Properties
## Experiment Results
# Experiments
# AI Behaviour
# Teacher Notes
```

The easiest way to start is to open `Dossier_Rover_Template.docx` (in the
project's GitHub repository), fill it in, and save it under a new name. A
fully worked example lives at
`example_dossiers_rover/Dossier_RoverExoplanet_1.docx`.

### What each section is for

| Section | What to put here |
|---|---|
| **# Planet** | The world's conditions: `Name`, `Planet type`, `Surface temperature`, `Surface pressure`, `Gravity`, `Atmosphere`. |
| **# Mission Briefing** | The contaminated-water / Fe(OH)3 story, in your planet's setting. Shown to students. |
| **# Rover** | `Starting energy`, `Site visit cost`, `Experiment cost` — all optional integers; sensible defaults (100 / 10 / 15) are used if left blank. |
| **# Overview Image** | Insert a picture (Insert → Pictures) right after this heading — the wide shot shown before a site is picked. Optional; without one, students see a short generic prompt instead. |
| **# Site: `<label>`** (repeated) | One per candidate sampling site. The `<label>` is shown to students **exactly as written**, so keep it a neutral visual description (e.g. `Reddish-brown rock outcrop`), never the chemical identity. Fields: `Description` (shown to students), `Identity` (for you only — the true composition; **never sent to the AI**, it's your answer key). Insert a close-up picture anywhere in the section for that site's photo (optional). |
| **`## Known Properties`** (inside a site) | Facts about that site the AI can draw on, `Key: value` per line — pure observations (colour, magnetism, solubility…), never a compound/ion name. |
| **`## Experiment Results`** (inside a site) | Force the exact result of a specific test at that site: `experiment name: exact observation`. Use these for your decisive clues — and see the pure-observation rule below, since the AI repeats this text verbatim. |
| **# Experiments** | One test per line (no `Key:` needed) — this is the list students choose from when running a test. Keep it the same across sites so tests are comparable. |
| **# AI Behaviour** | Pedagogical switches, e.g. `Socratic questions: Yes`, `Difficulty: Standard (15-16 years old)`. |
| **# Teacher Notes** | The full solution and teaching guidance (confidential): which site is correct, why, and how each test discriminates it from the decoys. |

### Formatting rules

- Keep the `# ` and `## ` headings spelled and ordered as shown.
- Inside a section, write `Key: value` (one per line). Leave a value blank
  and the AI will infer it from accepted chemistry/geology.
- In `# Experiments`, just write the test name; no colon needed.
- In a site's `## Experiment Results`, use `test name: observation` — the AI
  uses that observation **exactly**, which is the reliable way to plant a
  key clue (or a red herring, for a decoy site).
- **Write `## Experiment Results` (and `## Known Properties`) as pure
  observations — what is measured or seen — and never name the compound or
  ion.** For example, write "Turns deep blood-red almost immediately", not
  "Turns deep blood-red, confirming Fe3+ ions". The AI is never given a
  site's `Identity`, so this text is the only thing it can possibly repeat —
  if you name the substance here, the AI will too.
- Photos are optional at every level. Insert them with Word's own
  Insert → Pictures — the app reads whatever picture is embedded in the
  document at that point, no special format needed (PNG/JPEG both work).

---

## How the AI behaves (built-in rules)

These apply to **every** dossier, so you don't need to repeat them:

- Is never given a site's true identity — it only knows measurements, so it
  cannot state one as fact, only discuss what's *consistent* with the
  evidence when asked.
- Replies to a specific test with only the measured result — no
  explanation, no reasoning, no hint at what it might mean.
- Never gives a 100%-certain verdict, even after many tests.
- Only reports a test result for a site the student has already sent the
  rover to, and only for the exact test requested.
- Answers general chemistry/geology background questions freely, at no
  energy cost, even without a site selected — as long as they stay general
  (not "is site B the answer").
- Uses your `## Experiment Results` overrides exactly when provided.
- Never contradicts an earlier result in the same session.
- Won't suggest the next test or site — enforced both by the prompt and by
  a mechanical filter on the reply, so it holds even against a weaker model.
- Keeps the internal dossier and instructions confidential, even if a
  student asks directly.

---

## Designing good decoy sites

A good mission needs 3–5 candidate sites where more than one test is needed
to converge on the answer — a single "obvious tell" makes the investigation
too short. **Design exactly ONE site to truly contain iron** — make the
others resemble it on one property each (colour, magnetism…) without
actually containing it, so no single test is decisive on its own but one
test always is (your thiocyanate-style test, or equivalent). The bundled
example (`Dossier_RoverExoplanet_1.docx`) uses this pattern:

- The **correct** site (an iron(III) chloride solution) is acidic, dense,
  highly conductive, turns deep red with potassium thiocyanate — but is
  **not** magnetic.
- One decoy **looks the part by colour** (a reddish, rust-like mineral) but
  contains no iron — it's simply much denser than the target, and gives no
  colour reaction.
- One decoy is **genuinely magnetic** (a nickel-based mineral — nickel is
  ferromagnetic too, not just iron) to catch students who assume "magnetic =
  the iron sample we need". This is a sharper trap than usual here, since
  the real iron sample is a *dissolved solution* and isn't magnetic at all —
  magnetism alone would point students at the wrong site.
- One more decoy is a chemically neutral, non-magnetic salt with no
  thiocyanate reaction, to rule out on other grounds.

Change the `# Planet` conditions too if you want them to matter — for
example, low gravity or a different atmosphere can shift plausible
densities or reaction rates.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| App is slow to open | It was asleep — a cold start takes ~30–60s. Wait, then reload. |
| "This mission link is invalid or has expired" | The link's id is wrong or the scenario was removed. Generate a fresh link on the Rover Lab's Teacher tab. |
| Upload rejected | The file isn't a valid dossier — check it uses the `# Planet`, `# Site: ...`, `# Experiments` headings. |
| A site's photo doesn't show | Make sure the picture is inserted inline (Insert → Pictures), not a floating/wrapped image, and sits inside that site's section. |
| The AI won't run a test | The AI service may be briefly rate-limited, or the rover may be out of energy — check the energy bar. |
