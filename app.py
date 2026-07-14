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

import streamlit as st

st.set_page_config(
    page_title="Scientific AI Laboratory",
    page_icon="🔬",
    layout="wide",
)

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
    teacher = st.Page("views/Teacher.py", title="Teacher", icon="👩‍🏫", url_path="Teacher")
    student = st.Page("views/Student.py", title="Student Laboratory", icon="🧪", url_path="Student")
    st.navigation([home, teacher, student]).run()
