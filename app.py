#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 15:59:05 2026

@author: andrea
"""

"""
Scientific AI Laboratory
Version 0.1

Main application / navigation controller.
"""

import os

import streamlit as st

st.set_page_config(
    page_title="Scientific AI Laboratory",
    page_icon="🔬",
    layout="wide",
)

# On Streamlit Community Cloud there is no .env file; configuration comes from
# the app's Secrets. Mirror them into environment variables so the framework-
# free modules (which read os.getenv) work both locally (.env) and deployed.
try:
    for _key, _value in st.secrets.items():
        os.environ.setdefault(_key, str(_value))
except Exception:
    pass

# Student links carry ?lab=<id>. In that case we show ONLY the chat page with
# the navigation hidden — the Teacher page is not even registered, so students
# cannot reach the confidential scenario details.
if st.query_params.get("lab") is not None:

    chat = st.Page(
        "views/Student.py",
        title="Student Laboratory",
        icon="🧪",
        default=True,
    )
    st.navigation([chat], position="hidden").run()

else:

    home = st.Page("views/Home.py", title="Home", icon="🔬", default=True)
    tutors = st.Page("views/Tutors.py", title="AI Tutors", icon="🎓", url_path="Tutors")
    elsewhere = st.Page("views/RunElsewhere.py", title="Use in your own chatbot", icon="🔗", url_path="elsewhere")
    student = st.Page("views/Student.py", title="Chemistry Lab", icon="🧪", url_path="Student")
    teacher = st.Page("views/Teacher.py", title="Teacher", icon="👩‍🏫", url_path="Teacher")
    guide = st.Page("views/Guide.py", title="Teacher Guide", icon="📖", url_path="Guide")
    st.navigation([home, tutors, elsewhere, student, teacher, guide]).run()
