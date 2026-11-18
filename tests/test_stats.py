"""Tests for statistics service and JSON store."""

from __future__ import annotations

from pathlib import Path

from algo_trainer.stats.service import StatsService
from algo_trainer.stats.store import JsonSubmissionStore


def test_only_fully_passed_submissions_count_as_solved(tmp_path: Path) -> None:
    store = JsonSubmissionStore(tmp_path / "submissions.json")
    service = StatsService(store)

    service.record_submission(problem_id=1, tests_passed=0, tests_total=5, code="pass")
    service.record_submission(problem_id=2, tests_passed=4, tests_total=5, code="pass")
    stats = service.get_statistics()
    assert stats["total_submissions"] == 2
    assert stats["problems_solved"] == 0

    service.record_submission(problem_id=1, tests_passed=10, tests_total=5, code="ok")
    stats = service.get_statistics()
    assert stats["problems_solved"] == 1

    p1 = service.get_problem_stats(1)
    assert p1["best_score"] == [5, 5]
    assert p1["solved"] is True

    service.reset_statistics()
    assert service.get_statistics()["total_submissions"] == 0
