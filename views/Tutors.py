#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI Tutors: pick a pre-prompted tutor (e.g. Emmy) and chat with it."""

import streamlit as st

from modules import tutors, llm

st.title("🎓 AI Tutors")

items = tutors.list_tutors()

if not items:
    st.info("No tutors are configured yet.")
    st.stop()

# Pick a tutor.
labels = {f'{it["icon"]} {it["title"]}': it["id"] for it in items}
choice = st.selectbox("Choose a tutor", list(labels.keys()))
tutor_id = labels[choice]
tutor = tutors.get_tutor(tutor_id)

st.caption(tutor["description"])

with st.expander("⚡ Run this tutor in your own (stronger) chatbot"):
    st.markdown(
        "This app uses a **free AI model**. You can run the very same tutor in a "
        "stronger chatbot (ChatGPT, Claude, Gemini, Copilot…) instead:\n\n"
        "1. Open a **new, empty chat** there.\n"
        "2. **Copy the whole prompt below** (copy button, top-right of the box).\n"
        "3. Paste it as your **first message** and send it — the tutor will greet "
        "you and start guiding you."
    )
    st.code(tutors.load_standalone(tutor_id), language="text")

if not llm.is_configured():
    st.error(
        f"The AI is not configured yet (provider: **{llm.PROVIDER}**). "
        "Add the provider's API key to the app's secrets / `.env`."
    )
    st.stop()

# One separate conversation per tutor, reset when you switch tutors.
history_key = f"tutor_history::{tutor_id}"
if st.session_state.get("current_tutor") != tutor_id or history_key not in st.session_state:
    st.session_state["current_tutor"] = tutor_id
    st.session_state[history_key] = [
        {"role": "assistant", "content": tutor["greeting"]}
    ]

history = st.session_state[history_key]

# Replay the conversation so far.
for message in history:
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message["content"])

student_message = st.chat_input("Type your reply…")

if student_message:

    with st.chat_message("user"):
        st.markdown(student_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply = llm.chat(
                    tutors.load_prompt(tutor_id),
                    student_message,
                    history=history,
                    max_tokens=tutor.get("max_tokens"),
                    history_turns=tutor.get("history_turns"),
                )
            except llm.LabConfigError as error:
                reply = f"⚠️ Configuration problem: {error}"
            except Exception as error:  # noqa: BLE001 - surface any API error
                reply = f"⚠️ The tutor could not reply: {error}"
        st.markdown(reply)

    history.append({"role": "user", "content": student_message})
    history.append({"role": "assistant", "content": reply})

if len(history) > 1:
    if st.button("🔄 Restart session"):
        st.session_state[history_key] = [
            {"role": "assistant", "content": tutor["greeting"]}
        ]
        st.rerun()
