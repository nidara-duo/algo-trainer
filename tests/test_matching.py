"""Unit tests for output comparison strategies."""

from __future__ import annotations

from algo_trainer.domain.enums import MatchMode
from algo_trainer.domain.matching import (
    compare_approx,
    compare_exact,
    compare_sorted,
    get_matcher,
)


def test_compare_exact_primitives_and_none_regression() -> None:
    assert compare_exact(42, 42) is True
    assert compare_exact(None, None) is True
    # Regression: old _compare_exact treated int 0 as equal to None in lists.
    assert compare_exact(0, None) is False
    assert compare_exact([0, 1], [None, 1]) is False
    assert compare_exact(False, 0) is False
    assert compare_exact(True, 1) is False


def test_compare_exact_nested_structures() -> None:
    assert compare_exact([[1, 2], [3]], [[1, 2], [3]]) is True
    assert compare_exact([[1, 2], [3]], [[1, 2], [4]]) is False
    assert compare_exact({"a": [1, 2]}, {"a": [1, 2]}) is True


def test_compare_sorted() -> None:
    assert compare_sorted([3, 1, 2], [1, 2, 3]) is True
    assert compare_sorted([["b", "a"], ["c"]], [["c"], ["a", "b"]]) is True
    assert compare_sorted([1, 2], [1, 2, 3]) is False


def test_compare_approx() -> None:
    assert compare_approx(1.0000001, 1.0) is True
    assert compare_approx(1.001, 1.0) is False
    assert compare_approx([0.1 + 0.2], [0.3]) is True
    assert compare_approx(True, 1.0) is False


def test_matcher_registry() -> None:
    assert get_matcher(MatchMode.EXACT) is compare_exact
    assert get_matcher(MatchMode.SORTED) is compare_sorted
    assert get_matcher(MatchMode.APPROX) is compare_approx
