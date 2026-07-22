#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Landing page for the Scientific AI Laboratory."""

import streamlit as st

st.title("🔬 Scientific AI Laboratory")

st.markdown(
    """
Welcome to the **Scientific AI Laboratory** — a set of AI-powered activities
for science teaching.

- 🎓 **AI Tutors** — chat with a subject tutor (e.g. *Emmy*, the Socratic physics
  research guide) that walks you through an experiment step by step.
- 🧪 **Chemistry Lab** — identify an unknown sample by designing experiments.
  Inside, choose **Student** (pick a scenario, or open your teacher's link) or
  **Teacher** (set up and share an investigation).
- 🛰️ **Rover Lab** — remotely drive a rover's AI-embedded laboratory across
  an exoplanet, pick a sampling site from its photos, and run physical tests
  to work out which one most likely holds the iron(III) chloride sample
  mission control needs. Runs on a limited energy budget. Same **Student** /
  **Teacher** structure as the Chemistry Lab.

Use the menu on the left to choose an activity.
"""
)
