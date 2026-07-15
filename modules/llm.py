#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 16:01:30 2026

@author: andrea
"""

"""
llm.py

Provider-agnostic connector for the Scientific AI Laboratory.

Knows NOTHING about Streamlit. Two public entry points share one engine:
  - run_experiment(...)  -> the chemistry lab (hidden-dossier simulation)
  - chat(...)            -> the generic tutors (Emmy, and future tutors)

------------------------------------------------------------------
Choosing a provider
------------------------------------------------------------------
All supported providers speak the OpenAI-compatible chat API, so a single
`openai` client library talks to every one of them.

    LAB_PROVIDER=groq        # Groq       -> FREE tier (default)
    LAB_PROVIDER=gemini      # Gemini     -> free tier (region-restricted)
    LAB_PROVIDER=cerebras    # Cerebras   -> FREE tier
    LAB_PROVIDER=openrouter  # OpenRouter -> has :free models
    LAB_PROVIDER=openai      # OpenAI     -> paid
    LAB_PROVIDER=ollama      # Local model

    LAB_MODEL=...            # optional: override the model in one place

------------------------------------------------------------------
Staying inside free limits (important for a public, shared key)
------------------------------------------------------------------
    LAB_MAX_TOKENS=700       # cap the length of each AI reply
    LAB_HISTORY_TURNS=6      # only resend the last N turns (not the whole session)
    LAB_FALLBACKS=groq:llama-3.1-8b-instant
                             # if the primary model errors/rate-limits, try these next.
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
# NOTE: model names change over time. Check each provider's current model list
# and adjust LAB_MODEL / LAB_FALLBACKS in .env if one is renamed or retired.
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        # Plain instruct model that reliably keeps the answer hidden. Reasoning
        # models on Groq (gpt-oss, qwen3) tend to leak the sample identity or
        # dump their <think> reasoning, so they are NOT used here.
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "api_key_env": "CEREBRAS_API_KEY",
        "default_model": "gpt-oss-120b",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_model": "deepseek/deepseek-chat-v3.1:free",
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


# Read all configuration in ONE place.
PROVIDER = os.getenv("LAB_PROVIDER", "groq").strip().lower()
MODEL = os.getenv("LAB_MODEL", "").strip()  # empty -> use the provider default
MAX_TOKENS = int(os.getenv("LAB_MAX_TOKENS", "700"))
HISTORY_TURNS = int(os.getenv("LAB_HISTORY_TURNS", "6"))
FALLBACKS = os.getenv("LAB_FALLBACKS", "groq:llama-3.1-8b-instant")


class LabConfigError(RuntimeError):
    """Raised when no provider is configured with a usable API key."""


def _provider_config():
    if PROVIDER not in PROVIDERS:
        raise LabConfigError(
            f"Unknown LAB_PROVIDER '{PROVIDER}'. "
            f"Choose one of: {', '.join(PROVIDERS)}."
        )
    return PROVIDERS[PROVIDER]


def is_configured():
    """True if the primary provider has everything it needs to run."""
    try:
        cfg = _provider_config()
    except LabConfigError:
        return False
    if PROVIDER == "ollama":
        return True
    return bool(os.getenv(cfg["api_key_env"]))


def _attempt_chain():
    """Ordered (provider, model) attempts: the primary first, then fallbacks."""
    primary_cfg = PROVIDERS.get(PROVIDER)
    chain = []
    if primary_cfg:
        chain.append((PROVIDER, MODEL or primary_cfg["default_model"]))

    for entry in FALLBACKS.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        provider, model = entry.split(":", 1)  # split on FIRST ':' (models have '/' and ':')
        provider = provider.strip().lower()
        model = model.strip()
        if provider in PROVIDERS:
            chain.append((provider, model or PROVIDERS[provider]["default_model"]))

    return chain


def _client_for(provider):
    """Build an OpenAI-compatible client for a provider, or None if no key."""
    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["api_key_env"]) or ("ollama" if provider == "ollama" else None)
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=cfg["base_url"])


def _complete(system_prompt, message, history=None, max_tokens=None, history_turns=None):
    """
    Core completion with provider fallback. Shared by run_experiment and chat.

    Tries the primary model first; on any error (including a 429 rate-limit) it
    falls back to the next configured model, so a shared free key hitting its
    cap degrades gracefully instead of failing.
    """
    cap = MAX_TOKENS if max_tokens is None else max_tokens
    turns = HISTORY_TURNS if history_turns is None else history_turns

    # Keep only the most recent turns to bound token use per request.
    trimmed = history or []
    if turns > 0 and len(trimmed) > 2 * turns:
        trimmed = trimmed[-2 * turns:]

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(trimmed)
    messages.append({"role": "user", "content": message})

    tried_any = False
    errors = []
    for provider, model in _attempt_chain():
        client = _client_for(provider)
        if client is None:
            continue  # no key for this provider — skip it
        tried_any = True
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
                max_tokens=cap,
            )
            return response.choices[0].message.content
        except Exception as error:  # noqa: BLE001 - try the next fallback
            errors.append(f"{provider}/{model}: {error}")
            continue

    if not tried_any:
        raise LabConfigError(
            f"No API key found for provider '{PROVIDER}' (or any fallback). "
            f"Set {_provider_config()['api_key_env']} in your .env file."
        )
    raise RuntimeError(
        "All AI providers failed (they may be rate-limited — try again shortly).\n"
        + "\n".join(errors)
    )


def run_experiment(investigation, experiment, history=None):
    """Chemistry lab: simulate one experiment and return the technician's reply."""
    return _complete(build_system_prompt(investigation), experiment, history=history)


def chat(system_prompt, message, history=None, max_tokens=None, history_turns=None):
    """
    Generic tutor chat: reply to `message` using an arbitrary system prompt.

    Same provider fallback and history trimming as the lab, but the caller can
    raise the reply cap (a tutor may need to share code) and widen the history
    window (a tutor tracks state across a long session).
    """
    return _complete(
        system_prompt,
        message,
        history=history,
        max_tokens=max_tokens,
        history_turns=history_turns,
    )
