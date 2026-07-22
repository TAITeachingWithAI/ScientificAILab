#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rover_dossier_reader.py

Reads a teacher's Rover Lab dossier (.docx) and converts it into a structured
'investigation' dictionary, the same idea as dossier_reader.py but for the
rover activity: instead of one hidden unknown sample, the dossier lists
several candidate sampling sites (one of which is the real target), each with
its own confidential identity, known properties and experiment results, and
an optional embedded close-up photo. A single embedded overview photo (under
'# Overview Image') is shown before any site is picked.

Heading convention (same '# Heading' idea as dossier_reader.py):

    # Planet
    # Mission Briefing
    # Rover
    # Overview Image
    # Site: <label>            (repeated, one per candidate site)
        Description: ...
        Identity: ...
        ## Known Properties
        Key: value
        ## Experiment Results
        Experiment name: exact observation
    # Experiments
    # AI Behaviour
    # Teacher Notes

Pictures are read wherever they are inserted inline in the document (right
after '# Overview Image', or anywhere inside a '# Site: ...' section) and are
base64-encoded, so the resulting dict stays plain-JSON serialisable (it can
go straight through the existing scenario store).
"""

import base64

from docx import Document
from docx.oxml.ns import qn

from modules.dossier_reader import parse_fields


DEFAULT_ENERGY = {
    "starting_energy": 100,
    "site_visit_cost": 10,
    "experiment_cost": 15,
}


def _first_int(value, default):
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else default


def _extract_paragraph_image(paragraph, document):
    """Returns the base64-encoded bytes of the first image embedded in this
    paragraph, or None. Word stores an inline picture as a <w:drawing> run
    containing a <a:blip r:embed="rIdN">; the actual bytes live in the
    document part related to that relationship id."""
    for run in paragraph.runs:
        for drawing in run._element.findall(".//" + qn("w:drawing")):
            for blip in drawing.findall(".//" + qn("a:blip")):
                r_id = blip.get(qn("r:embed"))
                if not r_id:
                    continue
                try:
                    part = document.part.related_parts[r_id]
                except KeyError:
                    continue
                return base64.b64encode(part.blob).decode("ascii")
    return None


def energy_config(rover_fields):
    """Normalises the '# Rover' section into ints, falling back to defaults
    for anything blank or unparsable."""
    return {
        "starting_energy": _first_int(
            rover_fields.get("Starting energy", ""), DEFAULT_ENERGY["starting_energy"]
        ),
        "site_visit_cost": _first_int(
            rover_fields.get("Site visit cost", ""), DEFAULT_ENERGY["site_visit_cost"]
        ),
        "experiment_cost": _first_int(
            rover_fields.get("Experiment cost", ""), DEFAULT_ENERGY["experiment_cost"]
        ),
    }


def read_rover_docx(uploaded_file, extract_images=True):
    """
    extract_images=False skips reading/base64-encoding embedded pictures
    entirely (all image fields come back None) — the text is otherwise
    identical. Use this for lightweight passes that only need e.g. the
    planet name (a teacher's scenario picker), since decoding every image in
    every built-in dossier just to build a label list is wasteful once
    dossiers carry full-resolution photos.
    """
    document = Document(uploaded_file)

    investigation = {
        "planet": {},
        "mission_briefing": "",
        "rover": dict(DEFAULT_ENERGY),
        "overview_image": None,
        "sites": [],
        "experiments": [],
        "ai_behaviour": {},
        "teacher_notes": "",
    }

    current = None  # planet / mission_briefing / rover / overview_image / site / experiments / ai_behaviour / teacher_notes
    buffer = []

    current_site = None
    site_sub = "main"  # main / known / results
    site_buffers = {"main": [], "known": [], "results": []}

    def flush_simple():
        nonlocal buffer
        if current == "planet":
            investigation["planet"] = parse_fields(buffer)
        elif current == "rover":
            investigation["rover"] = energy_config(parse_fields(buffer))
        elif current == "ai_behaviour":
            investigation["ai_behaviour"] = parse_fields(buffer)
        elif current == "mission_briefing":
            investigation["mission_briefing"] = "\n".join(
                line for line in buffer if line
            ).strip()
        elif current == "teacher_notes":
            investigation["teacher_notes"] = "\n".join(buffer)
        elif current == "experiments":
            investigation["experiments"] = [line for line in buffer if line]
        buffer = []

    def flush_site():
        nonlocal current_site, site_sub, site_buffers
        if current_site is not None:
            main_fields = parse_fields(site_buffers["main"])
            current_site["description"] = main_fields.get("Description", "")
            current_site["identity"] = main_fields.get("Identity", "")
            current_site["known_properties"] = parse_fields(site_buffers["known"])
            current_site["experiment_results"] = parse_fields(site_buffers["results"])
            investigation["sites"].append(current_site)
        current_site = None
        site_sub = "main"
        site_buffers = {"main": [], "known": [], "results": []}

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        lower = text.lower()
        image_b64 = _extract_paragraph_image(paragraph, document) if extract_images else None

        if lower == "# planet":
            flush_simple()
            flush_site()
            current = "planet"
            continue
        if lower == "# mission briefing":
            flush_simple()
            flush_site()
            current = "mission_briefing"
            continue
        if lower == "# rover":
            flush_simple()
            flush_site()
            current = "rover"
            continue
        if lower == "# overview image":
            flush_simple()
            flush_site()
            current = "overview_image"
            continue
        if lower.startswith("# site:"):
            flush_simple()
            flush_site()
            current = "site"
            current_site = {
                "name": text.split(":", 1)[1].strip(),
                "description": "",
                "identity": "",
                "known_properties": {},
                "experiment_results": {},
                "image": None,
            }
            continue
        if lower == "# experiments":
            flush_simple()
            flush_site()
            current = "experiments"
            continue
        if lower == "# ai behaviour":
            flush_simple()
            flush_site()
            current = "ai_behaviour"
            continue
        if lower == "# teacher notes":
            flush_simple()
            flush_site()
            current = "teacher_notes"
            continue

        if current == "overview_image":
            if image_b64 and investigation["overview_image"] is None:
                investigation["overview_image"] = image_b64
            continue

        if current == "site":
            if image_b64 and current_site["image"] is None:
                current_site["image"] = image_b64
            if lower == "## known properties":
                site_sub = "known"
                continue
            if lower == "## experiment results":
                site_sub = "results"
                continue
            site_buffers[site_sub].append(text)
            continue

        buffer.append(text)

    flush_simple()
    flush_site()

    return investigation
