#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
progress.py

Best-effort persistence of a tutor conversation, so a student NEVER loses their
work when the page reloads, the connection drops, or the app restarts.

Frameworkless (no Streamlit), like llm.py and store.py. The caller passes a
stable `key` (built from a per-student session id kept in the URL) plus the data
to store. Every function is wrapped so a storage failure can never break the
chat: it just means one autosave was skipped.

Backend is chosen with LAB_TRANSCRIPT_BACKEND (default "local"), independent of
the scenario STORE_BACKEND:
  - "local" -> data/transcripts/<key>.json on the server. Survives page reloads
               and dropped connections (the reported problem); a file written by
               one session is read back by the next. Reset only if the whole app
               container is rebooted/redeployed.
  - "s3"    -> <S3_TRANSCRIPT_PREFIX><key>.json on the configured bucket. More
               durable (survives reboots) but only if the S3 credentials allow
               writes. It defaults OFF because a failing autosave must never
               silently drop a student's work.
"""

import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "transcripts"

_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]")


def _safe(key):
    return _UNSAFE.sub("_", str(key))[:120]


def _backend():
    # Independent of the scenario STORE_BACKEND, and local by default so a
    # broken/blocked S3 can never silently lose a student's progress.
    return os.getenv("LAB_TRANSCRIPT_BACKEND", "local").strip().lower()


def _local_path(key):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{_safe(key)}.json"


_s3 = None


def _s3_client():
    global _s3
    if _s3 is None:
        import boto3
        from botocore.config import Config

        _s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
            region_name=os.getenv("S3_REGION", "auto"),
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
    return _s3


def _s3_key(key):
    prefix = os.getenv("S3_TRANSCRIPT_PREFIX", "transcripts/")
    return f"{prefix}{_safe(key)}.json"


def save(key, data):
    """Persist `data` (a JSON-serialisable dict) under `key`. Returns True on success."""
    try:
        blob = json.dumps(data, ensure_ascii=False).encode("utf-8")
        if _backend() in ("s3", "r2"):
            _s3_client().put_object(
                Bucket=os.environ["S3_BUCKET"],
                Key=_s3_key(key),
                Body=blob,
                ContentType="application/json",
            )
        else:
            _local_path(key).write_bytes(blob)
        return True
    except Exception:  # noqa: BLE001 - autosave must never break the chat
        return False


def load(key):
    """Return the stored dict for `key`, or None if it is absent or on any error."""
    try:
        if _backend() in ("s3", "r2"):
            from botocore.exceptions import ClientError

            try:
                obj = _s3_client().get_object(
                    Bucket=os.environ["S3_BUCKET"], Key=_s3_key(key)
                )
            except ClientError:
                return None
            return json.loads(obj["Body"].read().decode("utf-8"))
        path = _local_path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
