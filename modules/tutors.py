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
    "physics_emmy": {
        "kind": "socratic",
        "title": "Emmy — Physics Research Tutor",
        "icon": "🔭",
        "description": (
            "A Socratic tutor for physics experiments. Emmy guides you through the "
            "scientific method for an experiment of your choice — one question at a "
            "time. She won't hand you answers, but you can always ask her for a hint."
        ),
        "prompt_file": "physics_emmy.md",
        "greeting": (
            "**Stage 1/5: Research Question. Status: draft. Next: Hypothesis.**\n\n"
            "Hi, I'm Emmy, your scientific mentor. Whenever you're stuck, just ask "
            "me for help or a small hint — otherwise I'll keep nudging you with "
            "questions so you do the thinking. What physics experiment are you "
            "investigating?"
        ),
        "max_tokens": 1200,
        "history_turns": 15,
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
        "max_tokens": 900,    # ~300-word answers + the intro
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


# Prepended when a student pastes a tutor into their OWN chatbot.
_STANDALONE_HEADER = """\
[Paste this whole message as the FIRST message in a new, empty chat with any AI
assistant (ChatGPT, Claude, Gemini, Copilot, ...). It configures the assistant to
take on the role described below.]

Adopt the role defined in the instructions that follow and keep it for the entire
conversation. Begin immediately as those instructions say — for a tutor, send its
opening line; for a role-play, introduce yourself in character — then wait for the
student's reply. Follow every rule below on every turn.

===============================================================================

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


def get_tutor(tutor_id):
    return TUTORS.get(tutor_id)


def load_prompt(tutor_id):
    """Read the tutor's prompt file (a full prompt, or a $placeholder template)."""
    tutor = TUTORS[tutor_id]
    return (PROMPTS_DIR / tutor["prompt_file"]).read_text(encoding="utf-8")


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
    return wrap_standalone(load_prompt(tutor_id))
