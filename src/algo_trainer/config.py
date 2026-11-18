"""Application configuration and filesystem path resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _find_project_root(start: Path) -> Path:
    """Walk up from `start` until a directory with `pyproject.toml` and `data/problems` is found."""
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "data" / "problems").is_dir():
            return candidate
    return Path.cwd()


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Resolved filesystem paths for bundled content, web assets, and user state."""

    web_root: Path
    problems_dir: Path
    state_dir: Path

    @property
    def index_html(self) -> Path:
        return self.web_root / "index.html"

    @property
    def submissions_path(self) -> Path:
        return self.state_dir / "submissions.json"

    @classmethod
    def resolve(cls) -> AppPaths:
        env_root = os.environ.get("ALGO_TRAINER_ROOT")
        root = (
            Path(env_root).resolve() if env_root else _find_project_root(Path(__file__).resolve())
        )

        env_state = os.environ.get("ALGO_TRAINER_STATE_DIR")
        state_dir = Path(env_state).resolve() if env_state else root / "data"

        return cls(
            web_root=root,
            problems_dir=root / "data" / "problems",
            state_dir=state_dir,
        )


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    """Timeouts and output limits for sandboxed test execution."""

    per_test_timeout_s: float = 0.5
    total_timeout_s: float = 5.0
    max_stdout_bytes: int = 4096


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level application configuration."""

    paths: AppPaths
    execution: ExecutionConfig = ExecutionConfig()

    @classmethod
    def load(cls) -> AppConfig:
        return cls(paths=AppPaths.resolve())
