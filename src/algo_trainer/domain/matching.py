"""Output comparison strategies registered by MatchMode."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from algo_trainer.domain.enums import MatchMode

Matcher = Callable[[Any, Any], bool]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def compare_exact(got: Any, expected: Any) -> bool:
    """Compare values for exact structural equality (without int/None confusion)."""
    if got is None or expected is None:
        return got is None and expected is None

    if isinstance(got, bool) != isinstance(expected, bool):
        return False

    if isinstance(got, list) and isinstance(expected, list):
        if len(got) != len(expected):
            return False
        return all(compare_exact(g, e) for g, e in zip(got, expected, strict=True))

    if isinstance(got, dict) and isinstance(expected, dict):
        if got.keys() != expected.keys():
            return False
        return all(compare_exact(got[k], expected[k]) for k in got)

    return bool(got == expected)


def compare_sorted(got: Any, expected: Any) -> bool:
    """Compare lists ignoring element order (supports one level of nested lists)."""
    try:
        if isinstance(got, list) and isinstance(expected, list):
            if len(got) != len(expected):
                return False
            if got and isinstance(got[0], list):
                if not all(isinstance(x, list) for x in got + expected):
                    return False
                got_sorted = sorted(sorted(inner) for inner in got)
                expected_sorted = sorted(sorted(inner) for inner in expected)
                return got_sorted == expected_sorted
            return sorted(got) == sorted(expected)
        return compare_exact(got, expected)
    except (TypeError, ValueError):
        return False


def compare_approx(got: Any, expected: Any, tol: float = 1e-6) -> bool:
    """Compare floating-point values or nested lists within `tol`."""
    if _is_number(got) and _is_number(expected):
        return abs(float(got) - float(expected)) < tol

    if isinstance(got, list) and isinstance(expected, list):
        if len(got) != len(expected):
            return False
        return all(compare_approx(g, e, tol=tol) for g, e in zip(got, expected, strict=True))

    return compare_exact(got, expected)


def compare_wildcard_none(got: Any, expected: Any) -> bool:
    """Compare lists where `None` in `expected` matches any non-bool `int` (for random methods)."""
    if isinstance(got, list) and isinstance(expected, list):
        if len(got) != len(expected):
            return False
        return all(
            (e is None and _is_number(g) and isinstance(g, int)) or compare_exact(g, e)
            for g, e in zip(got, expected, strict=True)
        )
    return compare_exact(got, expected)


MATCHERS: dict[MatchMode, Matcher] = {
    MatchMode.EXACT: compare_exact,
    MatchMode.SORTED: compare_sorted,
    MatchMode.APPROX: compare_approx,
    MatchMode.WILDCARD_NONE: compare_wildcard_none,
}


def get_matcher(mode: MatchMode) -> Matcher:
    """Return the comparison strategy for the given MatchMode."""
    return MATCHERS[mode]
