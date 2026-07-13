#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 15:59:05 2026

@author: andrea
"""

"""
Scientific AI Laboratory
Version 0.1

Main application
"""

import streamlit as st


# ---------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------

st.set_page_config(
    page_title="Scientific AI Laboratory",
    page_icon="🔬",
    layout="wide"
)


# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("🔬 Scientific AI Laboratory")

st.subheader("Version 0.1")

st.write(
    """
Welcome!

This application simulates laboratory experiments on
unknown samples collected from exoplanets.

Teachers upload a confidential dossier.

Students investigate the sample by designing experiments.

The AI simulates the experimental results.
"""
)


st.divider()


# ---------------------------------------------------
# TEACHER SECTION
# ---------------------------------------------------

st.header("Teacher")

uploaded_file = st.file_uploader(
    "Upload dossier (.pdf or .docx)",
    type=["pdf", "docx"]
)

if uploaded_file is not None:

    st.success("Dossier uploaded successfully!")

    st.write("Filename:", uploaded_file.name)


st.divider()


# ---------------------------------------------------
# STUDENT SECTION
# ---------------------------------------------------

st.header("Student")

experiment = st.text_input(
    "Describe the experiment you want to perform:"
)

if st.button("Run Experiment"):

    if experiment == "":

        st.warning("Please describe an experiment.")

    else:

        st.info("Experiment requested:")

        st.write(experiment)

        st.success(
            "Later, the AI will simulate the experiment here."
        )