"""Statistics and session timing service."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from algo_trainer.domain.models import Submission
from algo_trainer.stats.store import SubmissionStore


def _utc_now() -> datetime:
    return datetime.now(UTC)


class StatsService:
    """Tracks problem-solving sessions, records submissions, and aggregates stats."""

    def __init__(self, store: SubmissionStore) -> None:
        self._store = store
        self._lock = Lock()
        self._session_start: datetime | None = None
        self._session_problem_id: int | None = None

    def start_problem(self, problem_id: int) -> None:
        self._session_start = _utc_now()
        self._session_problem_id = problem_id

    def record_submission(
        self,
        problem_id: int,
        tests_passed: int,
        tests_total: int,
        code: str,
        time_spent_seconds: int | None = None,
    ) -> Submission:
        total = max(0, int(tests_total))
        passed = max(0, min(int(tests_passed), total))

        if time_spent_seconds is not None:
            elapsed = max(0, int(time_spent_seconds))
        elif self._session_start is not None and self._session_problem_id == problem_id:
            elapsed = max(0, int((_utc_now() - self._session_start).total_seconds()))
        else:
            elapsed = 0

        submission = Submission(
            problem_id=problem_id,
            timestamp=_utc_now().isoformat(),
            time_spent_seconds=elapsed,
            tests_passed=passed,
            tests_total=total,
            code=code,
        )

        with self._lock:
            data = self._store.load()
            data["submissions"].append(asdict(submission))
            self._store.save(data)

            self._session_start = None
            self._session_problem_id = None
        return submission

    def get_statistics(self) -> dict[str, Any]:
        with self._lock:
            data = self._store.load()
        submissions: list[dict[str, Any]] = data.get("submissions", [])

        problems_solved: set[int] = set()
        total_time = 0
        submissions_by_problem: dict[int, int] = {}

        for sub in submissions:
            pid = sub.get("problem_id")
            if isinstance(pid, int):
                submissions_by_problem[pid] = submissions_by_problem.get(pid, 0) + 1
                passed = int(sub.get("tests_passed", 0))
                total = int(sub.get("tests_total", 0))
                if total > 0 and passed == total:
                    problems_solved.add(pid)
            total_time += int(sub.get("time_spent_seconds", 0))

        recent = submissions[-10:] if len(submissions) > 10 else list(submissions)
        return {
            "total_submissions": len(submissions),
            "problems_solved": len(problems_solved),
            "total_time_spent_seconds": total_time,
            "submissions_by_problem": submissions_by_problem,
            "recent_submissions": recent,
            "last_reset": data.get("last_reset"),
        }

    def get_problem_stats(self, problem_id: int) -> dict[str, Any]:
        with self._lock:
            data = self._store.load()
        submissions = [s for s in data.get("submissions", []) if s.get("problem_id") == problem_id]
        if not submissions:
            return {
                "attempts": 0,
                "best_score": [0, 0],
                "total_time": 0,
                "solved": False,
            }

        best = max(submissions, key=lambda s: int(s.get("tests_passed", 0)))
        best_passed = int(best.get("tests_passed", 0))
        best_total = int(best.get("tests_total", 0))

        return {
            "attempts": len(submissions),
            "best_score": [best_passed, best_total],
            "total_time": sum(int(s.get("time_spent_seconds", 0)) for s in submissions),
            "solved": best_total > 0 and best_passed == best_total,
            "last_attempt": submissions[-1].get("timestamp"),
        }

    def reset_statistics(self) -> dict[str, Any]:
        ts = _utc_now().isoformat()
        with self._lock:
            self._store.save({"submissions": [], "last_reset": ts})
            self._session_start = None
            self._session_problem_id = None
        return {
            "success": True,
            "message": "Statistics reset successfully",
            "reset_timestamp": ts,
        }
