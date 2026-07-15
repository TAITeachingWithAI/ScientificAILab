#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tutors.py

Registry of pre-prompted LLM tutors (Emmy the physics guide, and any future
tutors). Each tutor is defined by a bit of metadata plus a prompt file under
tutor_prompts/. Adding a new tutor is a few lines here + one prompt file.

Framework-free (no Streamlit), like llm.py and store.py.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "tutor_prompts"


# Each tutor:
#   title / icon / description  -> shown in the picker
#   greeting                    -> the tutor's opening message (shown first)
#   prompt_file                 -> the full system prompt (editable, in the repo)
#   max_tokens                  -> reply cap (tutors may need room for a code turn)
#   history_turns               -> how many past turns to resend (state tracking)
TUTORS = {
    "physics_emmy": {
        "title": "Emmy — Physics Research Tutor",
        "icon": "🔭",
        "description": (
            "A Socratic guide for the 'model an exoplanet' transit experiment. "
            "Emmy walks you through the scientific method one question at a time "
            "— she won't hand you answers, but you can always ask her for a hint."
        ),
        "prompt_file": "physics_emmy.md",
        "greeting": (
            "**Stage 1/5: Research Question. Status: draft. Next: Hypothesis.**\n\n"
            "Hi, I'm Emmy, your scientific mentor. Whenever you're stuck, just ask "
            "me for help or a small hint — otherwise I'll keep nudging you with "
            "questions so you do the thinking. What question are you investigating?"
        ),
        "max_tokens": 1200,   # room for a Stage-5 code turn
        "history_turns": 15,  # keep enough context to track the current stage
    },
}


def list_tutors():
    """Returns [{'id', 'title', 'icon', 'description'}, ...] for the picker."""
    return [
        {
            "id": tid,
            "title": t["title"],
            "icon": t["icon"],
            "description": t["description"],
        }
        for tid, t in TUTORS.items()
    ]


def get_tutor(tutor_id):
    return TUTORS.get(tutor_id)


def load_prompt(tutor_id):
    """Read the tutor's full system prompt from its file."""
    tutor = TUTORS[tutor_id]
    return (PROMPTS_DIR / tutor["prompt_file"]).read_text(encoding="utf-8")
