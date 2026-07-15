#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Give students the self-contained tutor prompt to run in their own chatbot."""

import streamlit as st

from modules import tutors

st.title("🔗 Use a tutor in your own chatbot")

st.markdown(
    """
This app runs on a **free AI model**, which keeps it free for everyone — but it's
probably not the most capable model available. If you'd like to run a tutor in a
**stronger chatbot of your choice** (ChatGPT, Claude, Gemini, Copilot, or your
school's AI), you can: the tutor is just a prompt.
"""
)

items = tutors.list_tutors()
if not items:
    st.info("No tutors are configured yet.")
    st.stop()

labels = {f'{it["icon"]} {it["title"]}': it["id"] for it in items}
choice = st.selectbox("Which tutor?", list(labels.keys()))
tutor_id = labels[choice]

st.markdown(
    """
**How to use it**

1. Open a **new, empty chat** in your chosen AI chatbot.
2. **Copy the whole prompt below** (use the copy button in the top-right of the box).
3. Paste it as your **first message** and send it.
4. The tutor will greet you and start guiding you — chat as normal from there.
"""
)

st.markdown("**The prompt:**")
st.code(tutors.load_standalone(tutor_id), language="text")

st.caption(
    "Tip: save the prompt somewhere, so you can reuse it next time without "
    "coming back here."
)
