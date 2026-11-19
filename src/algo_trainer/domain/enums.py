"""Domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class Difficulty(StrEnum):
    """Problem difficulty level."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class MatchMode(StrEnum):
    """Strategy used to compare actual output against expected output."""

    EXACT = "exact"
    SORTED = "sorted"
    APPROX = "approx"
    WILDCARD_NONE = "wildcard_none"


class Invocation(StrEnum):
    """How user code is invoked by the test harness."""

    FUNCTION = "function"
    CLASS = "class"
