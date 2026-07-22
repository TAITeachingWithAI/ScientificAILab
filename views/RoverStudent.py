#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rover student view — used when a student opens a teacher's link
( .../?rover=<id> ). Loads that scenario from the rover store and shows the
mission only (navigation hidden). The in-app version (with a scenario
picker) lives in RoverLab.py.
"""

import streamlit as st

from modules import llm, rover_ui

st.title("🛰️ Rover Lab — Student Mission")

st.markdown(rover_ui.LAB_INTRO)

lab_id = st.query_params.get("rover")
investigation = rover_ui.load_scenario(lab_id) if lab_id else None

if investigation is None:
    if lab_id:
        st.error("This mission link is invalid or has expired.")
    else:
        st.warning(
            "No mission selected. Ask your teacher for the rover link, "
            "or open the **Rover Lab** and pick a ready-made mission."
        )

elif not llm.is_configured():
    st.error(
        f"The AI laboratory is not configured yet (provider: **{llm.PROVIDER}**). "
        "Add the provider's API key to the app's secrets / `.env`."
    )

else:
    st.success("Mission ready.")
    rover_ui.render_rover_lab(investigation, history_key=f"rover::{lab_id or 'session'}")
