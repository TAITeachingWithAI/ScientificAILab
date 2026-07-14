#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Student chat view. Loaded on its own (hidden navigation) for student links."""

import streamlit as st

from modules.llm import run_experiment, is_configured, LabConfigError, PROVIDER
from modules.store import get_store

st.title("🧪 Student Laboratory")

st.write(
    """
Your task is to identify the unknown liquid.

Design experiments.

Interpret the observations.

Do not expect the AI to reveal the answer.
"""
)

store = get_store()

# Which scenario? The student arrives via a link like  .../?lab=<id>
lab_id = st.query_params.get("lab")

investigation = None
if lab_id:
    investigation = store.load(lab_id)

# Fallback: teacher testing in the same browser session (legacy hand-off).
if investigation is None:
    legacy = st.session_state.get("investigation", {})
    investigation = legacy.get("dossier")

# Reset the chat when the loaded scenario changes.
current_key = lab_id or ("session" if investigation is not None else None)
if st.session_state.get("current_lab") != current_key:
    st.session_state["current_lab"] = current_key
    st.session_state["lab_history"] = []

if investigation is None:

    if lab_id:
        st.error("This laboratory link is invalid or has expired.")
    else:
        st.warning(
            "No investigation selected. Ask your teacher for the laboratory link."
        )

elif not is_configured():

    st.error(
        f"The AI laboratory is not configured yet (provider: **{PROVIDER}**).\n\n"
        "Add the provider's API key to the `.env` file. See the README for details."
    )

else:

    st.success("Investigation ready.")

    if "lab_history" not in st.session_state:
        st.session_state["lab_history"] = []

    # Replay the conversation so far.
    for message in st.session_state["lab_history"]:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])

    experiment = st.chat_input("Describe the experiment you want to run...")

    if experiment:

        with st.chat_message("user"):
            st.markdown(experiment)

        with st.chat_message("assistant"):
            with st.spinner("Running experiment..."):
                try:
                    reply = run_experiment(
                        investigation,
                        experiment,
                        history=st.session_state["lab_history"],
                    )
                except LabConfigError as error:
                    reply = f"⚠️ Configuration problem: {error}"
                except Exception as error:  # noqa: BLE001 - surface any API error
                    reply = f"⚠️ The laboratory could not run this experiment: {error}"

            st.markdown(reply)

        st.session_state["lab_history"].append(
            {"role": "user", "content": experiment}
        )
        st.session_state["lab_history"].append(
            {"role": "assistant", "content": reply}
        )

    if st.session_state["lab_history"]:
        if st.button("🔄 Reset laboratory session"):
            st.session_state["lab_history"] = []
            st.rerun()
