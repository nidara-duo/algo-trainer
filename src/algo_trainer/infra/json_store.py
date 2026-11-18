"""Atomic JSON file persistence helpers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    """Read JSON from `path`, returning `default` if missing or corrupted."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json_atomic(path: Path, payload: Any) -> None:
    """Atomically write JSON `payload` to `path` via a temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, str(path))
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
