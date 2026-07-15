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
        "max_tokens": 1200,   # room for a Stage-5 code turn
        "history_turns": 15,  # keep enough context to track the current stage
    },
}


# Header prepended when a student pastes a tutor into their OWN chatbot. It tells
# a fresh assistant to adopt the role and open with the tutor's greeting.
_STANDALONE_HEADER = """\
[Paste this whole message as the FIRST message in a new, empty chat with any AI
assistant (ChatGPT, Claude, Gemini, Copilot, ...). It configures the assistant
to become the tutor described below.]

Adopt the role defined in the instructions that follow and keep it for the whole
conversation. Begin immediately by sending the "Opening line" exactly as written
in those instructions, and nothing else. Then wait for the student's reply, and
from then on follow every rule below on every turn.

===============================================================================

"""


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
    """Read the tutor's full system prompt from its file (used inside the app)."""
    tutor = TUTORS[tutor_id]
    return (PROMPTS_DIR / tutor["prompt_file"]).read_text(encoding="utf-8")


def load_standalone(tutor_id):
    """
    The self-contained version to paste into any external chatbot: the same
    prompt, wrapped with an instruction to take on the role and open the chat.
    """
    return _STANDALONE_HEADER + load_prompt(tutor_id)
