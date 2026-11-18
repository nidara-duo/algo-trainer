"""Submission persistence protocol and JSON-backed store."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from algo_trainer.infra.json_store import read_json, write_json_atomic


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class SubmissionStore(Protocol):
    """Persistence port for user submissions."""

    def load(self) -> dict[str, Any]: ...

    def save(self, data: dict[str, Any]) -> None: ...


class JsonSubmissionStore:
    """Atomic JSON file store for submissions."""

    def __init__(self, path: Path) -> None:
        self._path = path
        if not self._path.exists():
            self.save({"submissions": [], "last_reset": _utc_now_iso()})

    def load(self) -> dict[str, Any]:
        default = {"submissions": [], "last_reset": _utc_now_iso()}
        data = read_json(self._path, default)
        if not isinstance(data, dict) or not isinstance(data.get("submissions"), list):
            return default
        return data

    def save(self, data: dict[str, Any]) -> None:
        write_json_atomic(self._path, data)
