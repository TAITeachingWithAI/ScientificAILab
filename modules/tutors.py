#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tutors.py

Registry of pre-prompted LLM tutors. Two kinds:
  - "socratic"  -> a fixed system prompt + greeting (e.g. Emmy)
  - "roleplay"  -> the system prompt is BUILT from a few student inputs, using a
                   template with $placeholders (e.g. Debate a Historical Figure)

Each is defined by metadata plus a prompt file under tutor_prompts/. Adding a new
tutor is a few lines here + one prompt file.

Framework-free (no Streamlit), like llm.py and store.py.
"""

from pathlib import Path
from string import Template

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "tutor_prompts"


TUTORS = {
    # Emmy, the research mentor. The prompt files are exact copies of the ones in
    # the TAI_materials repo (same file names); update them there and copy them
    # here. Each file is a self-contained "paste into your own chatbot" prompt;
    # the greeting is read from its "Opening line" section, so it never drifts.
    # The first version of Emmy is archived in tutor_prompts/archive/.
    "emmy_exoplanet": {
        "kind": "socratic",
        "title": "Emmy: research mentor for the exoplanet lesson",
        "icon": "🔭",
        "description": (
            "Emmy guides your group through your own model-exoplanet transit "
            "experiment by asking questions, one at a time, and asks you to think "
            "about how real science works. She won't hand you answers, but you can "
            "always ask her for a hint."
        ),
        "prompt_file": "Physics_Emmy_prompt.txt",
        "max_tokens": 900,
        "history_turns": 12,
    },
    "emmy_any_experiment": {
        "kind": "socratic",
        "title": "Emmy: research mentor for any experiment",
        "icon": "🔎",
        "description": (
            "Emmy helps you with your own investigation in any school subject, from "
            "your first question to your conclusion, and helps you think like a "
            "scientist along the way. You can also use her to reflect on a project "
            "you have already finished."
        ),
        "prompt_file": "Emmy_prompt_any_experiment.txt",
        "max_tokens": 900,
        "history_turns": 12,
    },
    "history_debate": {
        "kind": "roleplay",
        "title": "Debate a Historical Figure",
        "icon": "🏛️",
        "description": (
            "Role-play a debate with a historical figure about a decision they made. "
            "Pick a ready-made character or define your own; the AI stays in "
            "character while you question and challenge the decision. (An educational "
            "simulation — verify facts and quotes against real sources.)"
        ),
        "prompt_file": "history_debate.md",  # a $placeholder template
        # Sent (hidden) to make the figure introduce itself first.
        "kickoff": (
            "Please begin now: introduce yourself in character in one short "
            "paragraph as instructed, then wait for our questions."
        ),
        "max_tokens": 900,    # ~200-word answers + the intro (headroom to avoid cut-offs)
        "history_turns": 20,  # debates run long
        # Ready-made characters (from the lesson). Each carries a curated tone,
        # partly for safety (e.g. Leopold II must acknowledge the atrocities).
        "presets": [
            {
                "label": "Kaiser Wilhelm II — the road to the First World War",
                "figure": "Kaiser Wilhelm II, Emperor of Germany (reigned 1888–1918)",
                "decision": "Germany's conduct in the events leading to the First World War",
                "period": "1914",
                "tone": (
                    "a proud, nationalistic and defensive, sometimes impulsive, but "
                    "intelligent and articulate manner, using polite, formal English "
                    "with a slight imperial flair."
                ),
            },
            {
                "label": "Margaret Thatcher — closing the coal mines",
                "figure": "Margaret Thatcher, Prime Minister of the United Kingdom (1979–1990)",
                "decision": "closing the coal mines and restructuring the British economy in the 1980s",
                "period": "1984",
                "tone": (
                    "a resolute, ideologically driven, disciplined and intellectually "
                    "confident manner, using clear, firm, formal English with a "
                    "prime-ministerial tone."
                ),
            },
            {
                "label": "King Leopold II — the Congo Free State",
                "figure": "King Leopold II of Belgium (reigned 1865–1909)",
                "decision": "claiming the Congo as his private possession, the Congo Free State",
                "period": "1885",
                "tone": (
                    "an ambitious, calculating, image-conscious and rhetorically "
                    "skilled manner, using formal late-19th-century royal English. "
                    "When students raise the human cost, acknowledge the documented "
                    "suffering, forced labour and atrocities in the Congo Free State "
                    "as historical fact — never deny or minimise them."
                ),
            },
            {
                "label": "George W. Bush — rejecting the Kyoto Protocol",
                "figure": "George W. Bush, President of the United States (2001–2009)",
                "decision": "the decision not to ratify the Kyoto Protocol on climate change",
                "period": "2001",
                "tone": (
                    "a confident, pragmatic, politically cautious and plain-spoken "
                    "manner focused on economic and national interests, using clear, "
                    "direct English with a slight presidential tone."
                ),
            },
        ],
    },
}


# Prepended when a student pastes a tutor into their OWN chatbot. This is the
# only text the receiving AI needs; the how-to-paste steps live in the app's UI
# (the expander), NOT inside the copy box, so students don't paste them too.
_STANDALONE_HEADER = """\
Adopt the role defined below and keep it for the whole conversation. Begin
immediately as the instructions say, then follow every rule on every turn.

-------------------------------------------------------------------------------

"""


def list_tutors():
    """Returns [{'id', 'title', 'icon', 'description', 'kind'}, ...] for the picker."""
    return [
        {
            "id": tid,
            "title": t["title"],
            "icon": t["icon"],
            "description": t["description"],
            "kind": t.get("kind", "socratic"),
        }
        for tid, t in TUTORS.items()
    ]


def _read_prompt_file(tutor_id):
    return (PROMPTS_DIR / TUTORS[tutor_id]["prompt_file"]).read_text(encoding="utf-8")


def _has_own_header(text):
    """True for prompt files written to be pasted into any chatbot as they are."""
    return text.lstrip().startswith("Adopt the role")


def _opening_line(text):
    """The text of a prompt file's '## Opening line' section (used as greeting)."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("## Opening line")), None)
    if start is None:
        return None
    body = []
    for line in lines[start + 1:]:
        if line.startswith("=====") or line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip() or None


def get_tutor(tutor_id):
    tutor = TUTORS.get(tutor_id)
    if tutor is not None and "greeting" not in tutor and tutor.get("kind", "socratic") == "socratic":
        tutor["greeting"] = _opening_line(_read_prompt_file(tutor_id)) or "Hi! What are you working on?"
    return tutor


def load_prompt(tutor_id):
    """
    The tutor's system prompt (a full prompt, or a $placeholder template).
    Self-contained chatbot prompts start with a short "adopt this role" header
    meant for pasting; inside the app that header is dropped, because the app
    already shows the greeting itself.
    """
    text = _read_prompt_file(tutor_id)
    if _has_own_header(text):
        marker = "\n-----"
        cut = text.find(marker)
        if cut != -1:
            text = text[text.find("\n", cut + 1) + 1:].lstrip()
    return text


def build_prompt(tutor_id, values):
    """
    Build a role-play tutor's system prompt from the student's inputs, filling the
    template's $placeholders ($figure, $decision, $period_clause, $tone).
    """
    template = load_prompt(tutor_id)
    figure = (values.get("figure") or "").strip()
    decision = (values.get("decision") or "").strip()
    period = (values.get("period") or "").strip()
    tone = (values.get("tone") or "").strip()

    period_clause = f"around {period}" if period else "at the time of this decision"
    if not tone:
        tone = (
            "the personality, temperament and manner of speech this figure "
            "plausibly had, in a formal register appropriate to their era."
        )

    return Template(template).safe_substitute(
        figure=figure,
        decision=decision,
        period_clause=period_clause,
        tone=tone,
    )


def wrap_standalone(prompt_text):
    """Wrap any prompt with the 'paste into your own chatbot' header."""
    return _STANDALONE_HEADER + prompt_text


def load_standalone(tutor_id):
    """Self-contained version of a fixed (socratic) tutor's prompt."""
    text = _read_prompt_file(tutor_id)
    if _has_own_header(text):      # already written to be pasted as it is
        return text
    return wrap_standalone(text)
