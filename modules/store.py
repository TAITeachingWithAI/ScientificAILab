#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
store.py

Scenario store for the Scientific AI Laboratory.

Both kinds of scenario go through the same interface so the rest of the app
never has to care where a scenario came from:

  - built-in scenarios  -> the .docx files shipped in the repo (read from disk)
  - uploaded scenarios  -> saved by a teacher at runtime

This module knows NOTHING about Streamlit (same rule as llm.py), so it can be
reused from any front-end.

Backends (chosen with STORE_BACKEND in .env):
  - "local"  -> saves uploads as JSON files in a local data/ folder (dev)
  - "s3"/"r2"-> saves uploads to any S3-compatible object storage
                (Cloudflare R2, AWS S3, Backblaze B2, MinIO)  (production)
"""

import os
import json
import time
import secrets
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

from modules.dossier_reader import read_docx


# Load .env here so this module is self-sufficient: the Teacher page imports
# store without importing llm, so we can't rely on llm.py having loaded it.
load_dotenv()


# Project root = the folder that contains app.py (one level above /modules).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Where the built-in dossiers live (shipped with the code).
BUILTIN_SOURCES = [PROJECT_ROOT / "Dossier_template.docx"]
BUILTIN_DIR = PROJECT_ROOT / "example_dossiers"

# Where uploaded scenarios are stored by the local backend.
DATA_DIR = PROJECT_ROOT / "data" / "scenarios"

BUILTIN_PREFIX = "b_"
UPLOAD_PREFIX = "u_"


# ------------------------------------------------------------------
# Helpers (framework-free, reusable)
# ------------------------------------------------------------------
def validate_investigation(investigation):
    """
    Returns (ok, message). Rejects files that clearly aren't dossiers, e.g. a
    Word document with none of the expected sections.
    """
    if not isinstance(investigation, dict):
        return False, "The file could not be read as a dossier."

    has_content = (
        bool(investigation.get("experiments"))
        or bool(investigation.get("sample"))
        or bool(investigation.get("planet"))
    )
    if not has_content:
        return False, (
            "This file doesn't look like a dossier. Make sure it uses the "
            "section headings, e.g. '# Planet', '# Unknown Sample', "
            "'# Experiments'."
        )
    return True, ""


def _scenario_label(investigation, fallback):
    """A short human label for the teacher's picker (never shown to students)."""
    planet = investigation.get("planet", {}) or {}
    sample = investigation.get("sample", {}) or {}
    name = planet.get("Name") or fallback
    identity = sample.get("Identity")
    return f"{name} — {identity}" if identity else str(name)


def _new_id():
    return UPLOAD_PREFIX + secrets.token_urlsafe(8)


def _make_payload(investigation, label):
    return {
        "label": label or _scenario_label(investigation, "Uploaded scenario"),
        "created_at": time.time(),
        "investigation": investigation,
    }


# ------------------------------------------------------------------
# Base store: built-in scenarios are handled the same way everywhere.
# Subclasses only implement save() and _upload_by_id().
# ------------------------------------------------------------------
class BaseScenarioStore:

    def _builtin_files(self):
        files = [p for p in BUILTIN_SOURCES if p.exists()]
        if BUILTIN_DIR.exists():
            files.extend(sorted(BUILTIN_DIR.glob("*.docx")))
        return files

    def list_builtin(self):
        """Returns a list of {'id', 'label'} for the teacher's menu."""
        items = []
        for path in self._builtin_files():
            try:
                investigation = read_docx(str(path))
            except Exception:
                continue
            items.append(
                {
                    "id": BUILTIN_PREFIX + path.stem.lower(),
                    "label": _scenario_label(investigation, path.stem),
                }
            )
        return items

    def _builtin_by_id(self, scenario_id):
        stem = scenario_id[len(BUILTIN_PREFIX):]
        for path in self._builtin_files():
            if path.stem.lower() == stem:
                return read_docx(str(path))
        return None

    def load(self, scenario_id):
        """Return the investigation dict for an id, or None if not found."""
        if not scenario_id:
            return None
        if scenario_id.startswith(BUILTIN_PREFIX):
            return self._builtin_by_id(scenario_id)
        if scenario_id.startswith(UPLOAD_PREFIX):
            return self._upload_by_id(scenario_id)
        return None

    # Subclasses must implement these.
    def save(self, investigation, label=None):
        raise NotImplementedError

    def _upload_by_id(self, scenario_id):
        raise NotImplementedError


# ------------------------------------------------------------------
# Local backend (development)
# ------------------------------------------------------------------
class LocalScenarioStore(BaseScenarioStore):
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save(self, investigation, label=None):
        scenario_id = _new_id()
        payload = _make_payload(investigation, label)
        path = self.data_dir / f"{scenario_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        return scenario_id

    def _upload_by_id(self, scenario_id):
        path = self.data_dir / f"{scenario_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("investigation")


# ------------------------------------------------------------------
# S3-compatible backend (production: Cloudflare R2 / AWS S3 / B2 / MinIO)
# ------------------------------------------------------------------
class S3ScenarioStore(BaseScenarioStore):
    def __init__(self):
        import boto3  # imported lazily so local dev doesn't need boto3
        from botocore.config import Config

        self.bucket = os.environ["S3_BUCKET"]
        self.prefix = os.getenv("S3_PREFIX", "scenarios/")
        endpoint = os.getenv("S3_ENDPOINT_URL") or None  # R2/Supabase need this; AWS leaves empty

        # Non-AWS S3 endpoints (Supabase, R2, MinIO) require path-style
        # addressing and SigV4.
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
            region_name=os.getenv("S3_REGION", "auto"),
            config=config,
        )

    def _key(self, scenario_id):
        return f"{self.prefix}{scenario_id}.json"

    def save(self, investigation, label=None):
        scenario_id = _new_id()
        payload = _make_payload(investigation, label)
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(scenario_id),
            Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
        return scenario_id

    def _upload_by_id(self, scenario_id):
        from botocore.exceptions import ClientError

        try:
            obj = self.client.get_object(
                Bucket=self.bucket, Key=self._key(scenario_id)
            )
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NoSuchBucket"):
                return None
            raise
        payload = json.loads(obj["Body"].read().decode("utf-8"))
        return payload.get("investigation")


# ------------------------------------------------------------------
# Factory + link helper
# ------------------------------------------------------------------
def get_store():
    """Returns the configured scenario store (STORE_BACKEND in .env)."""
    backend = os.getenv("STORE_BACKEND", "local").strip().lower()
    if backend == "local":
        return LocalScenarioStore()
    if backend in ("s3", "r2"):
        return S3ScenarioStore()
    raise NotImplementedError(
        f"Store backend '{backend}' is not supported. Use 'local' or 's3'."
    )


def build_share_link(scenario_id):
    """
    Full URL a teacher gives to students, e.g. .../?lab=<id>.

    The link points at the app root: because the ?lab param is present, the app
    opens the student-only view with navigation hidden.
    """
    base = os.getenv("APP_BASE_URL", "http://localhost:8501").rstrip("/")
    return f"{base}/?lab={quote(scenario_id, safe='')}"
