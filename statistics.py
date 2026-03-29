"""
Statistics Manager - collects and stores user solution statistics.

Saves statistics to data/submissions.json with the following structure:
{
    "submissions": [
        {
            "problem_id": 1,
            "timestamp": "2026-03-27T10:30:00Z",
            "time_spent_seconds": 120,
            "tests_passed": 5,
            "tests_total": 5,
            "code": "def two_sum(nums, target):..."
        }
    ],
    "last_reset": "2026-03-27T00:00:00Z"
}
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class StatisticsManager:
    """Manages collection and storage of user solution statistics."""

    def __init__(self, data_dir: str):
        self.__data_dir = Path(data_dir)
        self.__stats_path = self.__data_dir / "submissions.json"
        self.__current_session_start: Optional[datetime] = None
        self.__current_problem_id: Optional[int] = None
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create statistics file if it doesn't exist."""
        if not self.__stats_path.exists():
            self.__stats_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({"submissions": [], "last_reset": datetime.now().isoformat()})

    def _load_data(self) -> dict:
        """Load statistics from file."""
        try:
            with open(self.__stats_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"submissions": [], "last_reset": datetime.now().isoformat()}

    def _save_data(self, data: dict) -> None:
        """Save statistics to file atomically."""
        import tempfile
        import os

        fd, temp_path = tempfile.mkstemp(
            dir=str(self.__stats_path.parent),
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, str(self.__stats_path))
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def start_problem(self, problem_id: int) -> None:
        """
        Start tracking time for a problem.

        Args:
            problem_id: ID of the problem being attempted
        """
        self.__current_session_start = datetime.now()
        self.__current_problem_id = problem_id

    def record_submission(
        self,
        problem_id: int,
        tests_passed: int,
        tests_total: int,
        code: str,
        force_time_spent: Optional[int] = None
    ) -> dict:
        """
        Record a code submission with statistics.

        Args:
            problem_id: ID of the problem
            tests_passed: Number of tests passed
            tests_total: Total number of tests
            code: User's submitted code
            force_time_spent: Override time spent (for testing)

        Returns:
            Dictionary with submission details
        """

        if force_time_spent is not None:
            time_spent = force_time_spent
        elif self.__current_session_start:
            time_spent = int((datetime.now() - self.__current_session_start).total_seconds())
        else:
            time_spent = 0


        submission = {
            "problem_id": problem_id,
            "timestamp": datetime.now().isoformat(),
            "time_spent_seconds": time_spent,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "code": code,
        }


        data = self._load_data()
        data["submissions"].append(submission)
        self._save_data(data)


        self.__current_session_start = None
        self.__current_problem_id = None

        return submission

    def get_statistics(self) -> dict:
        """
        Get aggregated statistics.

        Returns:
            Dictionary with aggregated stats:
            - total_submissions: Total number of submissions
            - problems_solved: Number of unique problems solved
            - total_time_spent: Total time spent in seconds
            - submissions_by_problem: Dict of problem_id -> submission count
            - recent_submissions: Last 10 submissions
        """
        data = self._load_data()
        submissions = data.get("submissions", [])


        problems_solved = set()
        total_time = 0
        submissions_by_problem: dict[int, int] = {}

        for sub in submissions:
            pid = sub.get("problem_id")
            if pid:
                problems_solved.add(pid)
                submissions_by_problem[pid] = submissions_by_problem.get(pid, 0) + 1
            total_time += sub.get("time_spent_seconds", 0)


        recent = submissions[-10:] if len(submissions) > 10 else submissions

        return {
            "total_submissions": len(submissions),
            "problems_solved": len(problems_solved),
            "total_time_spent_seconds": total_time,
            "submissions_by_problem": submissions_by_problem,
            "recent_submissions": recent,
            "last_reset": data.get("last_reset"),
        }

    def get_problem_stats(self, problem_id: int) -> dict:
        """
        Get statistics for a specific problem.

        Args:
            problem_id: ID of the problem

        Returns:
            Dictionary with problem-specific stats
        """
        data = self._load_data()
        submissions = [
            s for s in data.get("submissions", [])
            if s.get("problem_id") == problem_id
        ]

        if not submissions:
            return {
                "attempts": 0,
                "best_score": (0, 0),
                "total_time": 0,
                "solved": False,
            }


        best = max(submissions, key=lambda s: s.get("tests_passed", 0))

        return {
            "attempts": len(submissions),
            "best_score": (best.get("tests_passed", 0), best.get("tests_total", 0)),
            "total_time": sum(s.get("time_spent_seconds", 0) for s in submissions),
            "solved": best.get("tests_passed", 0) == best.get("tests_total", 0),
            "last_attempt": submissions[-1].get("timestamp"),
        }

    def reset_statistics(self) -> dict:
        """
        Reset all statistics.

        Returns:
            Dictionary with reset confirmation
        """
        self._save_data({
            "submissions": [],
            "last_reset": datetime.now().isoformat()
        })
        self.__current_session_start = None
        self.__current_problem_id = None

        return {
            "success": True,
            "message": "Statistics reset successfully",
            "reset_timestamp": datetime.now().isoformat()
        }

    def export_submissions(self) -> list[dict]:
        """
        Export all submissions.

        Returns:
            List of all submission records
        """
        data = self._load_data()
        return data.get("submissions", [])
