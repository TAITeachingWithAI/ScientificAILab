#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teacher view: choose or upload a scenario and get a shareable student link."""

import os

import streamlit as st

from modules.dossier_reader import read_docx
from modules.store import get_store, validate_investigation, build_share_link


st.title("👩‍🏫 Teacher")

# Optional gate: if TEACHER_ACCESS_CODE is set, require it before showing
# anything. This stops students from opening the Teacher view (e.g. by editing
# the URL) and reading the answer. Leave it empty to disable (e.g. locally).
ACCESS_CODE = os.getenv("TEACHER_ACCESS_CODE", "").strip()
if ACCESS_CODE and st.session_state.get("teacher_ok") is not True:
    code = st.text_input("Teacher access code", type="password")
    if st.button("Enter"):
        if code == ACCESS_CODE:
            st.session_state["teacher_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect code.")
    st.stop()


store = get_store()


def show_summary(investigation):
    """Teacher-only preview of a scenario (students never see this)."""
    planet = investigation.get("planet", {}) or {}
    st.write("### Planet")
    st.write(f"**Name:** {planet.get('Name', '')}")
    st.write(f"**Type:** {planet.get('Planet type', '')}")
    st.write(f"**Temperature:** {planet.get('Surface temperature', '')}")
    st.write(f"**Pressure:** {planet.get('Surface pressure', '')}")
    st.write(f"**Gravity:** {planet.get('Gravity', '')}")
    st.write(f"**Atmosphere:** {planet.get('Atmosphere', '')}")
    st.divider()
    st.write(f"✅ {len(investigation.get('experiments', []))} experiments available")
    if investigation.get("override_results"):
        st.write(f"✅ {len(investigation['override_results'])} required results defined")


def show_link(scenario_id):
    link = build_share_link(scenario_id)
    st.success("Share this link with your students:")
    st.code(link, language=None)
    st.markdown(f"[Open the student laboratory ↗]({link})")


tab_builtin, tab_upload = st.tabs(["📚 Use a ready-made scenario", "⬆️ Upload your own"])

# ------------------------------------------------------------------
# Built-in scenarios
# ------------------------------------------------------------------
with tab_builtin:
    st.write("Choose one of the ready-made investigations.")

    builtins = store.list_builtin()

    if not builtins:
        st.info("No built-in scenarios were found.")
    else:
        labels = {b["label"]: b["id"] for b in builtins}
        choice = st.selectbox("Scenario", list(labels.keys()))
        scenario_id = labels[choice]

        show_link(scenario_id)

        with st.expander("Preview this scenario (confidential)"):
            show_summary(store.load(scenario_id))

# ------------------------------------------------------------------
# Uploaded scenarios
# ------------------------------------------------------------------
with tab_upload:
    st.write("Upload your own confidential dossier (.docx).")

    uploaded_file = st.file_uploader(
        "Choose the investigation dossier (.docx)",
        type=["docx"],
    )

    if uploaded_file is not None:

        # Save only once per uploaded file (the page reruns on every click).
        signature = (uploaded_file.name, uploaded_file.size)
        if st.session_state.get("upload_signature") != signature:
            investigation = read_docx(uploaded_file)
            ok, message = validate_investigation(investigation)
            st.session_state["upload_signature"] = signature
            if ok:
                st.session_state["upload_id"] = store.save(
                    investigation, label=uploaded_file.name
                )
                st.session_state["upload_error"] = None
            else:
                st.session_state["upload_id"] = None
                st.session_state["upload_error"] = message

        if st.session_state.get("upload_error"):
            st.error(st.session_state["upload_error"])
        elif st.session_state.get("upload_id"):
            scenario_id = st.session_state["upload_id"]
            st.success("✅ Dossier saved.")
            show_link(scenario_id)
            with st.expander("Preview this scenario (confidential)"):
                show_summary(store.load(scenario_id))
