#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rover Lab (in-app): choose Student or Teacher."""

import streamlit as st

from modules import llm, rover_ui
from modules.store import get_rover_store

st.title("🛰️ Rover Lab")
st.markdown(rover_ui.LAB_INTRO)

role = st.radio(
    "I am a…",
    ["🧪 Student", "👩‍🏫 Teacher"],
    horizontal=True,
    key="rover_role",
)

st.divider()

if role == "👩‍🏫 Teacher":
    rover_ui.render_teacher()

else:  # Student
    if not llm.is_configured():
        st.error(
            f"The AI laboratory is not configured yet (provider: **{llm.PROVIDER}**). "
            "Add the provider's API key to the app's secrets / `.env`."
        )
        st.stop()

    store = get_rover_store()
    builtins = store.list_builtin()

    if not builtins:
        st.info("No ready-made missions are available. Ask your teacher for a link.")
        st.stop()

    st.write(
        "Pick a mission and start exploring. "
        "*(If your teacher gave you a link, just open that link instead.)*"
    )
    labels = {b["label"]: b["id"] for b in builtins}
    choice = st.selectbox("Mission", list(labels.keys()))
    scenario_id = labels[choice]

    rover_ui.render_rover_lab(rover_ui.load_scenario(scenario_id), history_key=f"rover::{scenario_id}")
