#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 16:01:30 2026

@author: andrea
"""

"""
llm.py

Provider-agnostic connector for the Scientific AI Laboratory.

This module knows NOTHING about Streamlit. It receives the investigation
dictionary, the student's experiment and (optionally) the previous
conversation as plain arguments, and returns only the laboratory
technician's text reply.

That way the same connector works from the Streamlit app today, and from a
future web app, mobile app or API without any changes.

------------------------------------------------------------------
Choosing a provider
------------------------------------------------------------------
All supported providers speak the OpenAI-compatible chat API, so a single
`openai` client library talks to every one of them. You only change the
base URL, the API key and the model name.

Pick a provider by setting LAB_PROVIDER in your .env file:

    LAB_PROVIDER=gemini      # Google Gemini  -> has a FREE tier
    LAB_PROVIDER=groq        # Groq           -> has a FREE tier
    LAB_PROVIDER=openai      # OpenAI         -> paid, usage-based
    LAB_PROVIDER=ollama      # Local model    -> free, runs on your machine

...and the matching API key, e.g.:

    GEMINI_API_KEY=...
    GROQ_API_KEY=...
    OPENAI_API_KEY=...
    # Ollama needs no key, just a running `ollama serve`

Optionally override the model in one place:

    LAB_MODEL=gemini-2.0-flash
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

from modules.prompts import build_system_prompt


# Load the .env file (API keys, provider choice) once, when the module is
# imported. Never hard-code keys in the source.
load_dotenv()


# ------------------------------------------------------------------
# Provider registry
# ------------------------------------------------------------------
# Each entry only needs: where to send the request (base_url), which
# environment variable holds the key, and a sensible default model.
#
# NOTE: model names change over time. These are reasonable defaults for a
# free/cheap classroom setup, but check each provider's current model list
# and adjust LAB_MODEL in .env if one is renamed or retired.
PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openai": {
        "base_url": None,  # use the OpenAI SDK default endpoint
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": "OLLAMA_API_KEY",  # unused by Ollama; a placeholder is fine
        "default_model": "llama3.1",
    },
}


# Read the chosen provider / model in ONE place, so the whole app is
# reconfigured by editing a single line in .env.
PROVIDER = os.getenv("LAB_PROVIDER", "gemini").strip().lower()
MODEL = os.getenv("LAB_MODEL", "").strip()  # empty -> use the provider default


class LabConfigError(RuntimeError):
    """Raised when the provider or API key is not configured correctly."""


def _provider_config():
    if PROVIDER not in PROVIDERS:
        raise LabConfigError(
            f"Unknown LAB_PROVIDER '{PROVIDER}'. "
            f"Choose one of: {', '.join(PROVIDERS)}."
        )
    return PROVIDERS[PROVIDER]


def is_configured():
    """
    Returns True if the selected provider has everything it needs to run.

    Lets the UI show a friendly setup hint instead of crashing on the first
    experiment. Ollama runs locally and needs no key.
    """
    try:
        cfg = _provider_config()
    except LabConfigError:
        return False

    if PROVIDER == "ollama":
        return True

    return bool(os.getenv(cfg["api_key_env"]))


def _client():
    cfg = _provider_config()

    # Ollama ignores the key but the OpenAI client still requires a non-empty
    # string, so we fall back to a harmless placeholder.
    api_key = os.getenv(cfg["api_key_env"]) or ("ollama" if PROVIDER == "ollama" else None)

    if not api_key:
        raise LabConfigError(
            f"No API key found for provider '{PROVIDER}'. "
            f"Set {cfg['api_key_env']} in your .env file."
        )

    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    model = MODEL or cfg["default_model"]
    return client, model


def run_experiment(investigation, experiment, history=None):
    """
    Simulate one experiment and return only the technician's reply.

    Parameters
    ----------
    investigation : dict
        The parsed dossier (planet, sample, known_properties, experiments,
        override_results, ai_behaviour, teacher_notes).
    experiment : str
        The student's experiment request, in natural language.
    history : list[dict] | None
        Previous turns as OpenAI-style messages, e.g.
        [{"role": "user", "content": "..."},
         {"role": "assistant", "content": "..."}].
        Passing this lets the model respect rule #8 (never contradict a
        previous experiment).

    Returns
    -------
    str
        The laboratory technician's response.
    """
    client, model = _client()

    system_prompt = build_system_prompt(investigation)

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": experiment})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.4,  # low: keep the simulated physics consistent
    )

    return response.choices[0].message.content
