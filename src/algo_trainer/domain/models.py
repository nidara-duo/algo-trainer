"""Domain value objects and entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from algo_trainer.domain.enums import Difficulty, Invocation, MatchMode


@dataclass(frozen=True, slots=True)
class ArgumentSpec:
    """Function parameter specification."""

    name: str
    type: str


@dataclass(frozen=True, slots=True)
class TestCase:
    """Single input/expected-output test case."""

    __test__ = False

    args: tuple[Any, ...]
    expected: Any


@dataclass(frozen=True, slots=True)
class Problem:
    """Complete coding problem definition."""

    id: int
    title: str
    difficulty: Difficulty
    matchmode: MatchMode
    invocation: Invocation
    function: str
    arguments: tuple[ArgumentSpec, ...]
    return_type: str
    examples_count: int
    condition: str
    tests: tuple[TestCase, ...]
    solution: str | None = None


@dataclass(frozen=True, slots=True)
class ProblemSummary:
    """Lightweight problem projection for UI listing."""

    id: int
    title: str
    difficulty: Difficulty


@dataclass(frozen=True, slots=True)
class TestOutcome:
    """Execution result for a single test case."""

    __test__ = False

    test_num: int
    passed: bool
    args: Any = None
    expected: Any = None
    got: Any = None
    error: str | None = None
    stdout: str = ""


@dataclass(frozen=True, slots=True)
class RunReport:
    """Aggregated result of running all tests for a submission."""

    success: bool
    results: tuple[TestOutcome, ...]
    summary: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Submission:
    """Recorded user submission."""

    problem_id: int
    timestamp: str
    time_spent_seconds: int
    tests_passed: int
    tests_total: int
    code: str

    @property
    def is_solved(self) -> bool:
        return self.tests_total > 0 and self.tests_passed == self.tests_total
