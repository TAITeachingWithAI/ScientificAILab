#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chem_ui.py

Shared UI pieces for the Chemistry Lab, so the student chat and the teacher
setup render the same way whether they're reached in-app (Chemistry Lab page)
or via a student link (Student page).

This is a UI-layer module — unlike llm.py / store.py / tutors.py, it DOES import
Streamlit.
"""

import os
from pathlib import Path

import streamlit as st

from modules import llm
from modules.dossier_reader import read_docx
from modules.store import get_store, validate_investigation, build_share_link

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def render_lab_chat(investigation, history_key):
    """Render the experiment chat for a given scenario (one history per key)."""
    if history_key not in st.session_state:
        st.session_state[history_key] = []
    history = st.session_state[history_key]

    for message in history:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])

    experiment = st.chat_input("Describe the experiment you want to run…")

    if experiment:
        with st.chat_message("user"):
            st.markdown(experiment)
        with st.chat_message("assistant"):
            with st.spinner("Running experiment…"):
                try:
                    reply = llm.run_experiment(investigation, experiment, history=history)
                except llm.LabConfigError as error:
                    reply = f"⚠️ Configuration problem: {error}"
                except Exception as error:  # noqa: BLE001 - surface any API error
                    reply = f"⚠️ The laboratory could not run this experiment: {error}"
            st.markdown(reply)
        history.append({"role": "user", "content": experiment})
        history.append({"role": "assistant", "content": reply})

    if history:
        if st.button("🔄 Reset laboratory session", key=f"reset::{history_key}"):
            st.session_state[history_key] = []
            st.rerun()


def render_teacher():
    """Teacher setup: pick or upload a scenario, get a share link, read the guide."""
    access_code = os.getenv("TEACHER_ACCESS_CODE", "").strip()
    if access_code and st.session_state.get("teacher_ok") is not True:
        code = st.text_input("Teacher access code", type="password", key="teacher_code")
        if st.button("Enter", key="teacher_enter"):
            if code == access_code:
                st.session_state["teacher_ok"] = True
                st.rerun()
            else:
                st.error("Incorrect code.")
        st.stop()

    store = get_store()

    def show_summary(inv):
        """Full confidential dossier for the teacher — including the answer."""
        st.warning(
            "This shows the full dossier, including the sample's identity and your "
            "teacher notes. The app has no login, so anyone who opens this Teacher "
            "tab can see it — set a `TEACHER_ACCESS_CODE` (in the app secrets / "
            "`.env`) to keep it teacher-only."
        )

        sample = inv.get("sample", {}) or {}
        st.write("#### 🧪 Unknown sample (the answer)")
        if sample:
            for key, value in sample.items():
                st.write(f"**{key}:** {value}")
        else:
            st.write("_not specified_")

        planet = inv.get("planet", {}) or {}
        if planet:
            st.write("#### 🪐 Planet")
            for key, value in planet.items():
                st.write(f"**{key}:** {value}")

        known = inv.get("known_properties", {}) or {}
        if known:
            st.write("#### Known properties (students may discover these)")
            for key, value in known.items():
                st.write(f"**{key}:** {value}")

        experiments = inv.get("experiments", []) or []
        if experiments:
            st.write(f"#### Experiments ({len(experiments)})")
            for experiment in experiments:
                st.write(f"- {experiment}")

        overrides = inv.get("override_results", {}) or {}
        if overrides:
            st.write(f"#### Required results / overrides ({len(overrides)})")
            for key, value in overrides.items():
                st.write(f"**{key}:** {value}")

        behaviour = inv.get("ai_behaviour", {}) or {}
        if behaviour:
            st.write("#### AI behaviour")
            for key, value in behaviour.items():
                st.write(f"**{key}:** {value}")

        notes = (inv.get("teacher_notes", "") or "").strip()
        if notes:
            st.write("#### 📝 Teacher notes")
            st.write(notes)

    def show_link(scenario_id):
        link = build_share_link(scenario_id)
        st.success("Share this link with your students:")
        st.code(link, language=None)
        st.markdown(f"[Open the student laboratory ↗]({link})")

    tab_builtin, tab_upload = st.tabs(
        ["📚 Use a ready-made scenario", "⬆️ Upload your own"]
    )

    with tab_builtin:
        st.write(
            "Students can also pick these ready-made scenarios themselves on the "
            "**Student** tab — you only need to share a link for scenarios you "
            "upload yourself."
        )
        builtins = store.list_builtin()
        if not builtins:
            st.info("No built-in scenarios were found.")
        else:
            labels = {b["label"]: b["id"] for b in builtins}
            choice = st.selectbox("Scenario", list(labels.keys()), key="teacher_builtin")
            scenario_id = labels[choice]
            show_link(scenario_id)
            with st.expander("🔍 Full scenario details (confidential — includes the answer)"):
                show_summary(store.load(scenario_id))

    with tab_upload:
        st.write("Upload your own confidential dossier (.docx).")
        uploaded_file = st.file_uploader(
            "Choose the investigation dossier (.docx)", type=["docx"], key="teacher_upload"
        )
        if uploaded_file is not None:
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
                with st.expander("🔍 Full scenario details (confidential — includes the answer)"):
                    show_summary(store.load(scenario_id))

    with st.expander("📖 Teacher Guide — how to use the Chemistry Lab"):
        try:
            st.markdown((PROJECT_ROOT / "TEACHER_GUIDE.md").read_text(encoding="utf-8"))
        except FileNotFoundError:
            st.info("Teacher guide not found.")
