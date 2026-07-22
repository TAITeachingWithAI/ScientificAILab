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

# Rover Lab uses a separate namespace (different dossier shape: candidate
# sites + embedded photos instead of one unknown sample) so its scenarios
# never mix with the Chemistry Lab's in the teacher's builtin list.
ROVER_BUILTIN_SOURCES = []
ROVER_BUILTIN_DIR = PROJECT_ROOT / "example_dossiers_rover"
ROVER_DATA_DIR = PROJECT_ROOT / "data" / "rover_scenarios"
ROVER_BUILTIN_PREFIX = "rb_"
ROVER_UPLOAD_PREFIX = "ru_"


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


def _new_id(prefix=UPLOAD_PREFIX):
    return prefix + secrets.token_urlsafe(8)


def _make_payload(investigation, label):
    return {
        "label": label or _scenario_label(investigation, "Uploaded scenario"),
        "created_at": time.time(),
        "investigation": investigation,
    }


# ------------------------------------------------------------------
# Base store: built-in scenarios are handled the same way everywhere.
# Subclasses only implement save() and _upload_by_id().
#
# Parameterised so the same class can serve two independent namespaces (the
# Chemistry Lab and the Rover Lab): each gets its own builtin folder, id
# prefixes, and dossier reader, so their scenarios never mix and an id from
# one can never accidentally resolve in the other.
# ------------------------------------------------------------------
class BaseScenarioStore:

    def __init__(
        self,
        builtin_sources=BUILTIN_SOURCES,
        builtin_dir=BUILTIN_DIR,
        builtin_prefix=BUILTIN_PREFIX,
        upload_prefix=UPLOAD_PREFIX,
        reader=read_docx,
        list_reader=None,
    ):
        self.builtin_sources = builtin_sources
        self.builtin_dir = builtin_dir
        self.builtin_prefix = builtin_prefix
        self.upload_prefix = upload_prefix
        self.reader = reader
        # A cheaper reader used only to build the scenario picker (just needs
        # the planet name). Defaults to the full reader; the rover store
        # overrides this to skip decoding every dossier's embedded photos,
        # which would otherwise happen on every rerun for every dossier.
        self.list_reader = list_reader or reader

    def _builtin_files(self):
        files = [p for p in self.builtin_sources if p.exists()]
        if self.builtin_dir.exists():
            files.extend(sorted(self.builtin_dir.glob("*.docx")))
        return files

    def list_builtin(self):
        """
        Returns a list of {'id', 'label'} for the teacher's menu.

        The label is the planet name only (never the sample identity), because
        the Teacher page is public — showing the answer here would let students
        read it. The confidential answers live in ANSWER_KEY.md.
        """
        items = []
        for path in self._builtin_files():
            try:
                investigation = self.list_reader(str(path))
            except Exception:
                continue
            planet = investigation.get("planet", {}) or {}
            label = planet.get("Name") or path.stem
            items.append(
                {
                    "id": self.builtin_prefix + path.stem.lower(),
                    "label": label,
                }
            )
        return items

    def _builtin_by_id(self, scenario_id):
        stem = scenario_id[len(self.builtin_prefix):]
        for path in self._builtin_files():
            if path.stem.lower() == stem:
                return self.reader(str(path))
        return None

    def load(self, scenario_id):
        """Return the investigation dict for an id, or None if not found."""
        if not scenario_id:
            return None
        if scenario_id.startswith(self.builtin_prefix):
            return self._builtin_by_id(scenario_id)
        if scenario_id.startswith(self.upload_prefix):
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
    def __init__(self, data_dir=DATA_DIR, **kwargs):
        super().__init__(**kwargs)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save(self, investigation, label=None):
        scenario_id = _new_id(self.upload_prefix)
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
    def __init__(self, s3_prefix=None, **kwargs):
        super().__init__(**kwargs)
        import boto3  # imported lazily so local dev doesn't need boto3
        from botocore.config import Config

        self.bucket = os.environ["S3_BUCKET"]
        self.prefix = s3_prefix or os.getenv("S3_PREFIX", "scenarios/")
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
        scenario_id = _new_id(self.upload_prefix)
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
    """Returns the configured Chemistry Lab scenario store (STORE_BACKEND in .env)."""
    backend = os.getenv("STORE_BACKEND", "local").strip().lower()
    if backend == "local":
        return LocalScenarioStore()
    if backend in ("s3", "r2"):
        return S3ScenarioStore()
    raise NotImplementedError(
        f"Store backend '{backend}' is not supported. Use 'local' or 's3'."
    )


def get_rover_store():
    """Returns the configured Rover Lab scenario store (its own namespace)."""
    from modules.rover_dossier_reader import read_rover_docx

    backend = os.getenv("STORE_BACKEND", "local").strip().lower()
    kwargs = dict(
        builtin_sources=ROVER_BUILTIN_SOURCES,
        builtin_dir=ROVER_BUILTIN_DIR,
        builtin_prefix=ROVER_BUILTIN_PREFIX,
        upload_prefix=ROVER_UPLOAD_PREFIX,
        reader=read_rover_docx,
        # Dossier photos can be several MB each; don't decode every image in
        # every built-in dossier just to list planet names in a picker.
        list_reader=lambda path: read_rover_docx(path, extract_images=False),
    )
    if backend == "local":
        return LocalScenarioStore(data_dir=ROVER_DATA_DIR, **kwargs)
    if backend in ("s3", "r2"):
        s3_prefix = os.getenv("S3_ROVER_PREFIX", "rover_scenarios/")
        return S3ScenarioStore(s3_prefix=s3_prefix, **kwargs)
    raise NotImplementedError(
        f"Store backend '{backend}' is not supported. Use 'local' or 's3'."
    )


def build_share_link(scenario_id, param="lab"):
    """
    Full URL a teacher gives to students, e.g. .../?lab=<id> (or ?rover=<id>).

    The link points at the app root: because the query param is present, the
    app opens the student-only view with navigation hidden.
    """
    base = os.getenv("APP_BASE_URL", "http://localhost:8501").rstrip("/")
    return f"{base}/?{param}={quote(scenario_id, safe='')}"
