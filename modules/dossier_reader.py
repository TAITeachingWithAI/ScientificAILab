#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 16:01:42 2026

@author: andrea
"""

"""
dossier_reader.py

Reads the teacher's Word dossier and separates it into sections.
"""

"""
dossier_reader.py

Reads the teacher's Word dossier and converts it into a structured
'investigation' dictionary.
"""

from docx import Document


def read_docx(uploaded_file):

    doc = Document(uploaded_file)

    text = ""

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return parse_dossier(text)


def parse_fields(lines):
    """
    Converts

    Density:
    1.2 g/mL

    into

    {"Density":"1.2 g/mL"}
    """

    data = {}

    current_key = None

    for line in lines:

        line = line.strip()

        if line == "":
            continue

        if ":" in line:

            key, value = line.split(":", 1)

            key = key.strip()

            value = value.strip()

            if value != "":
                data[key] = value
                current_key = None

            else:
                data[key] = ""
                current_key = key

        elif current_key is not None:

            data[current_key] = line
            current_key = None

    return data


def parse_dossier(text):

    investigation = {

        "planet": {},

        "sample": {},

        "known_properties": {},

        "experiments": [],

        "override_results": {},

        "ai_behaviour": {},

        "teacher_notes": ""

    }

    current = None

    buffer = []

    def save_current():

        nonlocal buffer

        if current == "planet":
            investigation["planet"] = parse_fields(buffer)

        elif current == "sample":
            investigation["sample"] = parse_fields(buffer)

        elif current == "known_properties":
            investigation["known_properties"] = parse_fields(buffer)

        elif current == "override_results":
            investigation["override_results"] = parse_fields(buffer)

        elif current == "ai_behaviour":
            investigation["ai_behaviour"] = parse_fields(buffer)

        elif current == "teacher_notes":
            investigation["teacher_notes"] = "\n".join(buffer)

        elif current == "experiments":

            experiments = []

            for line in buffer:

                line = line.strip()

                if line == "":
                    continue

                experiments.append(line)

            investigation["experiments"] = experiments

        buffer = []

    for line in text.splitlines():

        stripped = line.strip()

        lower = stripped.lower()

        if lower == "# planet":

            save_current()

            current = "planet"

            continue

        elif lower == "# unknown sample":

            save_current()

            current = "sample"

            continue

        elif lower == "# known properties":

            save_current()

            current = "known_properties"

            continue

        elif lower == "# experiments":

            save_current()

            current = "experiments"

            continue

        elif lower == "# override results":

            save_current()

            current = "override_results"

            continue

        elif lower == "# ai behaviour":

            save_current()

            current = "ai_behaviour"

            continue

        elif lower == "# teacher notes":

            save_current()

            current = "teacher_notes"

            continue

        buffer.append(stripped)

    save_current()

    return investigation