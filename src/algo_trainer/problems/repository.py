"""Problem repository protocol and YAML-backed implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from algo_trainer.domain.errors import ProblemNotFoundError, ProblemValidationError
from algo_trainer.domain.models import Problem, ProblemSummary
from algo_trainer.problems.yaml_loader import load_problem_yaml


class ProblemRepository(Protocol):
    """Read-only repository of coding problems."""

    def list_summaries(self) -> list[ProblemSummary]: ...

    def get_by_id(self, problem_id: int) -> Problem: ...

    def list_all(self) -> list[Problem]: ...


class YamlProblemRepository:
    """In-memory repository populated directly from `.yaml` problem files."""

    def __init__(self, problems_dir: Path) -> None:
        self._problems_dir = problems_dir
        self._problems: dict[int, Problem] = {}

    def load(self) -> None:
        """Scan `problems_dir` and load all `.yaml` files."""
        loaded: dict[int, Problem] = {}
        if not self._problems_dir.is_dir():
            self._problems = loaded
            return

        files = sorted(self._problems_dir.glob("*.yaml"), key=lambda p: p.name)
        for path in files:
            problem = load_problem_yaml(path)
            if problem.id in loaded:
                raise ProblemValidationError(path, f"duplicate problem id {problem.id}")
            loaded[problem.id] = problem

        self._problems = loaded

    def list_summaries(self) -> list[ProblemSummary]:
        return [
            ProblemSummary(id=p.id, title=p.title, difficulty=p.difficulty)
            for p in sorted(self._problems.values(), key=lambda p: p.id)
        ]

    def get_by_id(self, problem_id: int) -> Problem:
        problem = self._problems.get(problem_id)
        if problem is None:
            raise ProblemNotFoundError(problem_id)
        return problem

    def list_all(self) -> list[Problem]:
        return sorted(self._problems.values(), key=lambda p: p.id)
