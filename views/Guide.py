#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Renders the (public-safe) teacher guide inside the app."""

from pathlib import Path

import streamlit as st

GUIDE = Path(__file__).resolve().parent.parent / "TEACHER_GUIDE.md"

try:
    st.markdown(GUIDE.read_text(encoding="utf-8"))
except FileNotFoundError:
    st.error("Teacher guide not found.")
