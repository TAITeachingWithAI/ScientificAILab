#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Student chat view — used when a student opens a teacher's link ( .../?lab=<id> ).
Loads that scenario from the store and shows the chat only (navigation hidden).
The in-app version (with a scenario picker) lives in ChemistryLab.py.
"""

import streamlit as st

from modules import llm, chem_ui
from modules.store import get_store

st.title("🧪 Student Laboratory")

st.write(
    """
Your task is to identify the unknown liquid.
Design experiments, interpret the observations, and reason toward the answer —
the AI won't reveal it.
"""
)

store = get_store()

lab_id = st.query_params.get("lab")
investigation = store.load(lab_id) if lab_id else None

# Fallback: teacher testing in the same browser session (legacy hand-off).
if investigation is None:
    investigation = st.session_state.get("investigation", {}).get("dossier")

if investigation is None:
    if lab_id:
        st.error("This laboratory link is invalid or has expired.")
    else:
        st.warning(
            "No investigation selected. Ask your teacher for the laboratory link, "
            "or open the **Chemistry Lab** and pick a ready-made scenario."
        )

elif not llm.is_configured():
    st.error(
        f"The AI laboratory is not configured yet (provider: **{llm.PROVIDER}**). "
        "Add the provider's API key to the app's secrets / `.env`."
    )

else:
    st.success("Investigation ready.")
    chem_ui.render_lab_chat(investigation, history_key=f"lab::{lab_id or 'session'}")
