#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI Tutors: pick a pre-prompted tutor and chat with it.

Two kinds:
  - socratic  -> fixed prompt + greeting (Emmy)
  - roleplay  -> a short setup form builds the prompt (Debate a Historical Figure)
"""

import secrets

import streamlit as st

from modules import tutors, llm, ui, progress

st.title("🎓 AI Tutors")

items = tutors.list_tutors()
if not items:
    st.info("No tutors are configured yet.")
    st.stop()

labels = {f'{it["icon"]} {it["title"]}': it["id"] for it in items}
choice = st.selectbox("Choose a tutor", list(labels.keys()))
tutor_id = labels[choice]
tutor = tutors.get_tutor(tutor_id)

st.caption(tutor["description"])

if not llm.is_configured():
    st.error(
        f"The AI is not configured yet (provider: **{llm.PROVIDER}**). "
        "Add the provider's API key to the app's secrets / `.env`."
    )
    st.stop()

history_key = f"tutor_history::{tutor_id}"
prompt_key = f"rp_prompt::{tutor_id}"
label_key = f"rp_label::{tutor_id}"

# --- Never lose a student's work -------------------------------------------
# Keep a per-student session id in the URL (?sid=...). Because it lives in the
# URL it survives a page reload or a dropped connection, and the transcript is
# saved after every turn, so the student can always pick up where they left off,
# even if the app itself restarts.
sid = st.query_params.get("sid")
if not sid:
    sid = secrets.token_urlsafe(6)
    st.query_params["sid"] = sid
save_key = f"{sid}__{tutor_id}"


def _restore_once():
    """On a fresh page load, reload this student's saved conversation (if any)."""
    if history_key in st.session_state:
        return
    saved = progress.load(save_key)
    if not saved or not saved.get("history"):
        return
    st.session_state[history_key] = saved["history"]
    if saved.get("prompt"):  # a role-play in progress: restore its setup too
        st.session_state[prompt_key] = saved["prompt"]
        if saved.get("label"):
            st.session_state[label_key] = saved["label"]


def _persist():
    """Autosave the current conversation. Does nothing when nothing has changed."""
    history = st.session_state.get(history_key)
    if not history:
        return
    seen_key = f"{save_key}__n"
    if st.session_state.get(seen_key) == len(history):
        return
    envelope = {"history": history}
    if st.session_state.get(prompt_key):
        envelope["prompt"] = st.session_state[prompt_key]
        envelope["label"] = st.session_state.get(label_key)
    if progress.save(save_key, envelope):
        st.session_state[seen_key] = len(history)


_restore_once()


def run_elsewhere_expander(standalone_prompt, verb="guiding you"):
    with st.expander("⚡ Run this in your own (stronger) chatbot"):
        st.markdown(
            "This app uses a **free AI model**. You can run the very same thing in a "
            "stronger chatbot (ChatGPT, Claude, Gemini, Copilot…) instead:\n\n"
            "1. Open a **new, empty chat** there.\n"
            "2. **Copy the whole prompt below** (copy button, top-right of the box).\n"
            f"3. Paste it as your **first message** and send it — it will start {verb}."
        )
        st.code(standalone_prompt, language="text")


def render_chat(system_prompt, input_placeholder):
    history = st.session_state[history_key]
    for message in history:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])

    user_message = st.chat_input(input_placeholder)
    if user_message:
        with st.chat_message("user"):
            st.markdown(user_message)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    reply = llm.chat(
                        system_prompt,
                        user_message,
                        history=history,
                        max_tokens=tutor.get("max_tokens"),
                        history_turns=tutor.get("history_turns"),
                    )
                except llm.LabConfigError as error:
                    reply = f"⚠️ Configuration problem: {error}"
                except Exception as error:  # noqa: BLE001 - surface any API error
                    reply = f"⚠️ The tutor could not reply: {error}"
            st.markdown(reply)
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": reply})


kind = tutor.get("kind", "socratic")

# ------------------------------------------------------------------
# Fixed-prompt tutors (Emmy)
# ------------------------------------------------------------------
if kind == "socratic":
    run_elsewhere_expander(tutors.load_standalone(tutor_id))

    if history_key not in st.session_state:
        st.session_state[history_key] = [
            {"role": "assistant", "content": tutor["greeting"]}
        ]

    ui.ai_note()
    st.caption("💾 Your progress is saved automatically — it's safe to reload this page.")
    render_chat(tutors.load_prompt(tutor_id), "Type your reply…")

    if len(st.session_state[history_key]) > 1:
        if st.button("🔄 Restart session"):
            st.session_state[history_key] = [
                {"role": "assistant", "content": tutor["greeting"]}
            ]
            st.rerun()

# ------------------------------------------------------------------
# Role-play tutors (Debate a Historical Figure)
# ------------------------------------------------------------------
else:
    st.warning(
        "⚠️ This is an AI **simulation** of a historical figure for debate practice. "
        "It can be inaccurate or biased — treat its words as role-play, **not real "
        "quotations**, and verify any facts or quotes against real historical sources."
    )
    ui.ai_note()

    # --- setup form (until a debate is started) ---
    if prompt_key not in st.session_state:
        st.subheader("Set up your debate")

        presets = tutor.get("presets", [])
        OTHER = "✍️ Other — define your own"
        sel = st.selectbox(
            "Choose a character (or define your own)",
            [p["label"] for p in presets] + [OTHER],
        )

        if sel == OTHER:
            figure = st.text_input(
                "Historical figure & title",
                placeholder="e.g. Napoleon Bonaparte, Emperor of the French (1804–1815)",
            )
            decision = st.text_input(
                "The decision or action to debate",
                placeholder="e.g. invading Russia in 1812",
            )
            period = st.text_input(
                "When did it happen? (optional)", placeholder="e.g. 1812"
            )
            tone = ""
        else:
            preset = next(p for p in presets if p["label"] == sel)
            detail = f"**{preset['figure']}**\n\nDecision: {preset['decision']}"
            if preset.get("period"):
                detail += f"  \nWhen: {preset['period']}"
            st.info(detail)
            figure = preset["figure"]
            decision = preset["decision"]
            period = preset.get("period", "")
            tone = preset.get("tone", "")

        if st.button("Start the debate", type="primary"):
            if not figure.strip() or not decision.strip():
                st.error("Please fill in at least the figure and the decision.")
            else:
                system_prompt = tutors.build_prompt(
                    tutor_id,
                    {"figure": figure, "decision": decision, "period": period, "tone": tone},
                )
                with st.spinner("The figure is preparing to speak…"):
                    try:
                        intro = llm.chat(
                            system_prompt,
                            tutor["kickoff"],
                            history=[],
                            max_tokens=tutor.get("max_tokens"),
                            history_turns=tutor.get("history_turns"),
                        )
                    except Exception as error:  # noqa: BLE001
                        intro = f"⚠️ Could not start the debate: {error}"
                st.session_state[prompt_key] = system_prompt
                st.session_state[label_key] = f"{figure} — {decision}"
                st.session_state[history_key] = [
                    {"role": "assistant", "content": intro}
                ]
                st.rerun()

    # --- active debate ---
    else:
        st.caption(f"**Debating:** {st.session_state.get(label_key, '')}")

        if st.button("↩️ Change character / restart"):
            progress.save(save_key, {"history": []})  # clear so it isn't restored
            st.session_state[f"{save_key}__n"] = 0
            for key in (prompt_key, label_key, history_key):
                st.session_state.pop(key, None)
            st.rerun()

        run_elsewhere_expander(
            tutors.wrap_standalone(st.session_state[prompt_key]),
            verb="the debate (the figure will introduce itself)",
        )

        st.info(
            "Type **End of role** when you're done — the figure will step out of "
            "character and give a short factual summary."
        )

        st.caption("💾 Your progress is saved automatically — it's safe to reload this page.")
        render_chat(st.session_state[prompt_key], "Ask the figure a question…")


# Autosave the current conversation at the end of every run (cheap; skips when
# nothing changed). This is what lets a student reload and continue seamlessly.
_persist()
