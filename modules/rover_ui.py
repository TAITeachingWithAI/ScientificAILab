#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rover_ui.py

Shared UI pieces for the Rover Lab, so the student session and the teacher
setup render the same way whether they're reached in-app (Rover Lab page) or
via a student link (RoverStudent page). Mirrors chem_ui.py's shape.

This is a UI-layer module — unlike llm.py / store.py / rover_prompts.py, it
DOES import Streamlit.
"""

import base64
from pathlib import Path

import streamlit as st

from modules import llm, ui
from modules.rover_dossier_reader import read_rover_docx
from modules.rover_prompts import build_system_prompt, redact_suggestions
from modules.store import get_rover_store, validate_investigation, build_share_link

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LAB_INTRO = (
    "🛰️ **A rover has landed on an exoplanet where contaminated water was "
    "found.** Purifying it needs Fe(OH)3 — so mission control needs a sample "
    "rich in iron to begin with. \n\n"
    "You can't travel there, but the rover's onboard AI laboratory can run "
    "physical tests on any site you send it to: pH, density, conductivity, "
    "colour, magnetism… The rover only carries so much energy, so choose "
    "your tests wisely. **Which sample should be sent to Earth for analysis? There you can do further analysis and reactions to obtain Fe(OH)3**"
)


@st.cache_data(show_spinner="Loading mission…")
def load_scenario(scenario_id):
    """
    Cached wrapper around get_rover_store().load(). Dossiers can carry
    several MB of embedded photos, and Streamlit reruns the whole script on
    every interaction (every chat message, every button click) — without
    caching, that means re-parsing the .docx and re-decoding every image on
    every single rerun. Keyed on scenario_id, so switching scenarios still
    loads the right one.
    """
    return get_rover_store().load(scenario_id)


def _keys(history_key):
    return {
        "history": history_key,
        "energy": f"{history_key}::energy",
        "active": f"{history_key}::active",
        "visited": f"{history_key}::visited",
    }


def _init_session(history_key, investigation):
    k = _keys(history_key)
    if k["history"] not in st.session_state:
        st.session_state[k["history"]] = []
    if k["energy"] not in st.session_state:
        rover = investigation.get("rover") or {}
        st.session_state[k["energy"]] = rover.get("starting_energy", 100)
    if k["active"] not in st.session_state:
        st.session_state[k["active"]] = None
    if k["visited"] not in st.session_state:
        st.session_state[k["visited"]] = set()


def _reset_session(history_key, investigation):
    k = _keys(history_key)
    rover = investigation.get("rover") or {}
    st.session_state[k["history"]] = []
    st.session_state[k["energy"]] = rover.get("starting_energy", 100)
    st.session_state[k["active"]] = None
    st.session_state[k["visited"]] = set()


def _show_image_or_fallback(image_b64, fallback_text, caption=None):
    if image_b64:
        st.image(base64.b64decode(image_b64), caption=caption, use_container_width=True)
    else:
        st.info(f"🖼️ *(no photo provided)* {fallback_text}")


def _run_turn(investigation, history_key, message, transcript_label):
    """Sends one message to the AI lab and appends both sides to the chat log."""
    k = _keys(history_key)
    history = st.session_state[k["history"]]
    state = {
        "active_site": st.session_state[k["active"]],
        "visited": sorted(st.session_state[k["visited"]]),
        "energy_remaining": st.session_state[k["energy"]],
        "energy_starting": (investigation.get("rover") or {}).get("starting_energy", 100),
    }
    with st.spinner("Running…"):
        try:
            reply = llm.chat(build_system_prompt(investigation, state), message, history=history)
            reply, trimmed = redact_suggestions(reply)
            if trimmed:
                reply += (
                    "\n\n_(A suggestion for what to try next was removed — "
                    "that decision is yours.)_"
                )
        except llm.LabConfigError as error:
            reply = f"⚠️ Configuration problem: {error}"
        except Exception as error:  # noqa: BLE001 - surface any API error
            reply = f"⚠️ The rover's AI lab could not respond: {error}"
    history.append({"role": "user", "content": transcript_label})
    history.append({"role": "assistant", "content": reply})


def render_rover_lab(investigation, history_key):
    """Render the full Rover Lab session: overview/site imagery, energy
    gauge, site picker, experiment picker and general-question chat."""
    ui.ai_note()
    _init_session(history_key, investigation)
    k = _keys(history_key)

    rover_cfg = investigation.get("rover") or {}
    starting_energy = rover_cfg.get("starting_energy", 100)
    site_visit_cost = rover_cfg.get("site_visit_cost", 10)
    experiment_cost = rover_cfg.get("experiment_cost", 15)
    energy = st.session_state[k["energy"]]
    sites = investigation.get("sites") or []
    active_name = st.session_state[k["active"]]
    active_site = next((s for s in sites if s["name"] == active_name), None)

    st.progress(max(0, min(1.0, energy / starting_energy if starting_energy else 0)))
    st.caption(f"🔋 Rover energy: {max(energy, 0)} / {starting_energy}")

    if active_site is None:
        st.markdown("### 🪐 Landing site overview")
        _show_image_or_fallback(
            investigation.get("overview_image"),
            "Imagine a wide shot of the landing area with a few distinct "
            "features worth sampling, based on the descriptions below.",
        )
        st.markdown("**Candidate sampling sites** — pick one to send the rover to investigate:")
        for site in sites:
            visited = site["name"] in st.session_state[k["visited"]]
            afford = visited or energy >= site_visit_cost
            cost_label = "free (already visited)" if visited else f"costs {site_visit_cost} energy"
            if st.button(
                f"🔍 {site['name']} — {cost_label}",
                key=f"{history_key}::visit::{site['name']}",
                disabled=not afford,
            ):
                if not visited:
                    st.session_state[k["energy"]] = energy - site_visit_cost
                    st.session_state[k["visited"]].add(site["name"])
                st.session_state[k["active"]] = site["name"]
                st.rerun()
        if sites and not any(
            s["name"] in st.session_state[k["visited"]] or energy >= site_visit_cost for s in sites
        ):
            st.warning("⚠️ Not enough energy left to send the rover to a new site.")
    else:
        if st.button("← Back to overview", key=f"{history_key}::back"):
            st.session_state[k["active"]] = None
            st.rerun()
        st.markdown(f"### 📍 {active_site['name']}")
        _show_image_or_fallback(
            active_site.get("image"),
            active_site.get("description") or "No description provided.",
        )
        if active_site.get("description"):
            st.write(active_site["description"])

        experiments = investigation.get("experiments") or []
        if experiments:
            col1, col2 = st.columns([3, 1])
            with col1:
                chosen_experiment = st.selectbox(
                    "Physical test to run on this site",
                    experiments,
                    key=f"{history_key}::experiment_choice",
                )
            with col2:
                st.write("")
                st.write("")
                run_clicked = st.button(
                    f"🧪 Run ({experiment_cost} energy)",
                    key=f"{history_key}::run_experiment",
                    disabled=energy < experiment_cost,
                )
            if energy < experiment_cost:
                st.warning("⚠️ Not enough energy left to run another test.")
            if run_clicked:
                st.session_state[k["energy"]] = energy - experiment_cost
                _run_turn(
                    investigation,
                    history_key,
                    f"Run this experiment on the currently selected site "
                    f"({active_site['name']}): {chosen_experiment}. Reply with "
                    f"ONLY the measured result, one short line — no "
                    f"explanation, no reasoning, no mention of what it might "
                    f"indicate.",
                    f"🧪 [{active_site['name']}] {chosen_experiment}",
                )
                st.rerun()

    st.divider()
    st.markdown("**Chat log**")
    for message in st.session_state[k["history"]]:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])

    question = st.chat_input("Ask the AI lab a general question (free — no energy cost)…")
    if question:
        _run_turn(investigation, history_key, question, question)
        st.rerun()

    if st.session_state[k["history"]]:
        if st.button("🔄 Reset rover session", key=f"reset::{history_key}"):
            _reset_session(history_key, investigation)
            st.rerun()


def render_teacher():
    """Teacher setup: pick or upload a rover scenario, get a share link."""
    ui.require_teacher_access()

    store = get_rover_store()

    def show_summary(inv):
        st.warning(
            "This shows the full dossier, including every site's true identity "
            "and your teacher notes. The app has no login, so anyone who opens "
            "this Teacher tab can see it — set a `TEACHER_ACCESS_CODE` (in the "
            "app secrets / `.env`) to keep it teacher-only."
        )

        planet = inv.get("planet", {}) or {}
        if planet:
            st.write("#### 🪐 Planet")
            for key, value in planet.items():
                st.write(f"**{key}:** {value}")

        if inv.get("mission_briefing"):
            st.write("#### 📜 Mission briefing")
            st.write(inv["mission_briefing"])

        rover_cfg = inv.get("rover") or {}
        st.write("#### 🔋 Rover energy")
        st.write(
            f"Starting energy: **{rover_cfg.get('starting_energy')}** · "
            f"Site visit cost: **{rover_cfg.get('site_visit_cost')}** · "
            f"Experiment cost: **{rover_cfg.get('experiment_cost')}**"
        )

        sites = inv.get("sites") or []
        st.write(f"#### 🧪 Candidate sites ({len(sites)}) — the answer")
        for site in sites:
            with st.expander(f"{site['name']}"):
                st.write(f"**Identity:** {site.get('identity') or '_not specified_'}")
                st.write(f"**Description shown to students:** {site.get('description')}")
                if site.get("known_properties"):
                    st.write("**Known properties:**")
                    for key, value in site["known_properties"].items():
                        st.write(f"- {key}: {value}")
                if site.get("experiment_results"):
                    st.write("**Fixed experiment results:**")
                    for key, value in site["experiment_results"].items():
                        st.write(f"- {key}: {value}")
                if site.get("image"):
                    st.image(base64.b64decode(site["image"]), width=200)

        experiments = inv.get("experiments") or []
        if experiments:
            st.write(f"#### Available experiments ({len(experiments)})")
            for experiment in experiments:
                st.write(f"- {experiment}")

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
        link = build_share_link(scenario_id, param="rover")
        st.success("Share this link with your students:")
        st.code(link, language=None)
        st.markdown(f"[Open the student rover lab ↗]({link})")

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
            choice = st.selectbox("Scenario", list(labels.keys()), key="rover_teacher_builtin")
            scenario_id = labels[choice]
            show_link(scenario_id)
            with st.expander("🔍 Full scenario details (confidential — includes the answer)"):
                show_summary(load_scenario(scenario_id))

    with tab_upload:
        st.write(
            "Upload your own confidential dossier (.docx) — see "
            "`Dossier_Rover_Template.docx` and `ROVER_TEACHER_GUIDE.md` in the "
            "project repository for the format, including how to embed the "
            "overview and site photos directly in the Word document."
        )
        uploaded_file = st.file_uploader(
            "Choose the rover dossier (.docx)", type=["docx"], key="rover_teacher_upload"
        )
        if uploaded_file is not None:
            signature = (uploaded_file.name, uploaded_file.size)
            if st.session_state.get("rover_upload_signature") != signature:
                investigation = read_rover_docx(uploaded_file)
                ok, message = validate_investigation(investigation)
                st.session_state["rover_upload_signature"] = signature
                if ok:
                    st.session_state["rover_upload_id"] = store.save(
                        investigation, label=uploaded_file.name
                    )
                    st.session_state["rover_upload_error"] = None
                else:
                    st.session_state["rover_upload_id"] = None
                    st.session_state["rover_upload_error"] = message

            if st.session_state.get("rover_upload_error"):
                st.error(st.session_state["rover_upload_error"])
            elif st.session_state.get("rover_upload_id"):
                scenario_id = st.session_state["rover_upload_id"]
                st.success("✅ Dossier saved.")
                show_link(scenario_id)
                with st.expander("🔍 Full scenario details (confidential — includes the answer)"):
                    show_summary(load_scenario(scenario_id))

    with st.expander("📖 Teacher Guide — how to use the Rover Lab"):
        try:
            st.markdown((PROJECT_ROOT / "ROVER_TEACHER_GUIDE.md").read_text(encoding="utf-8"))
        except FileNotFoundError:
            st.info("Teacher guide not found.")
