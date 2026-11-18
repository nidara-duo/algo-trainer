"""Domain exceptions."""

from __future__ import annotations

from pathlib import Path


class AlgoTrainerError(Exception):
    """Base exception for all application errors."""


class ProblemNotFoundError(AlgoTrainerError):
    """Raised when a problem with the requested ID does not exist."""

    def __init__(self, problem_id: int) -> None:
        self.problem_id = problem_id
        super().__init__(f"Problem with ID {problem_id} not found")


class ProblemValidationError(AlgoTrainerError):
    """Raised when a problem YAML file fails schema or data validation."""

    def __init__(self, source: Path | str, reason: str) -> None:
        self.source = source
        self.reason = reason
        super().__init__(f"Invalid problem '{source}': {reason}")
