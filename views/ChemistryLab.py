#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chemistry Lab (in-app): choose Student or Teacher."""

import streamlit as st

from modules import llm, chem_ui
from modules.store import get_store

st.title("🧪 Chemistry Lab")
st.write(
    "Identify an unknown liquid by designing experiments and interpreting the "
    "observations. The AI simulates the lab — it won't reveal the answer."
)

role = st.radio(
    "I am a…",
    ["🧪 Student", "👩‍🏫 Teacher"],
    horizontal=True,
)

st.divider()

if role == "👩‍🏫 Teacher":
    chem_ui.render_teacher()

else:  # Student
    if not llm.is_configured():
        st.error(
            f"The AI laboratory is not configured yet (provider: **{llm.PROVIDER}**). "
            "Add the provider's API key to the app's secrets / `.env`."
        )
        st.stop()

    store = get_store()
    builtins = store.list_builtin()

    if not builtins:
        st.info("No ready-made scenarios are available. Ask your teacher for a link.")
        st.stop()

    st.write(
        "Pick an investigation and start experimenting. "
        "*(If your teacher gave you a link, just open that link instead.)*"
    )
    labels = {b["label"]: b["id"] for b in builtins}
    choice = st.selectbox("Investigation", list(labels.keys()))
    scenario_id = labels[choice]

    chem_ui.render_lab_chat(store.load(scenario_id), history_key=f"lab::{scenario_id}")
