"""
API - Bridge between JavaScript (pywebview) and Python backend.
"""

import traceback
from pathlib import Path

from problem_repository import ProblemRepository
from code_runner import CodeRunner
from submissions import StatisticsManager


class Api:
    """API class for pywebview JS bridge."""

    def __init__(self, base_dir: str):
        self.__base_dir = Path(base_dir)
        self.__data_dir = self.__base_dir / "data"
        self.__problems_dir = self.__data_dir / "problems"
        self.__db_path = self.__data_dir / "problems_db.json"

        self.__repo = ProblemRepository(
            problems_dir=str(self.__problems_dir),
            db_path=str(self.__db_path),
        )
        self.__repo.initialize()
        self.__runner = CodeRunner()
        

        self.__stats = StatisticsManager(str(self.__data_dir))

    def get_problems(self) -> dict:
        """Get list of all problems for UI display."""
        try:
            summaries = self.__repo.get_problem_summaries()
            return {"problems": summaries}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def get_problem(self, problem_id: int) -> dict:
        """Get full problem data by ID."""
        try:
            problem = self.__repo.get_by_id(problem_id)
            if problem is None:
                return {"error": f"Problem with ID {problem_id} not found"}
            return {"problem": problem}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def run_tests(self, problem_id: int, code: str) -> dict:
        """Run user code against problem tests."""
        try:
            problem = self.__repo.get_by_id(problem_id)
            if problem is None:
                return {"error": f"Problem with ID {problem_id} not found"}

            results = self.__runner.run_tests(code, problem)
            return results
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "summary": "Execution failed",
            }

    def start_problem_session(self, problem_id: int) -> dict:
        """Start tracking time for a problem."""
        try:
            self.__stats.start_problem(problem_id)
            return {"success": True, "problem_id": problem_id}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def record_submission(
        self,
        problem_id: int,
        tests_passed: int,
        tests_total: int,
        code: str
    ) -> dict:
        """Record a code submission with statistics."""
        try:
            submission = self.__stats.record_submission(
                problem_id=problem_id,
                tests_passed=tests_passed,
                tests_total=tests_total,
                code=code
            )
            return {"success": True, "submission": submission}
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def get_statistics(self) -> dict:
        """Get aggregated statistics."""
        try:
            stats = self.__stats.get_statistics()
            return stats
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def get_problem_statistics(self, problem_id: int) -> dict:
        """Get statistics for a specific problem."""
        try:
            stats = self.__stats.get_problem_stats(problem_id)
            return stats
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    def reset_statistics(self) -> dict:
        """Reset all statistics."""
        try:
            result = self.__stats.reset_statistics()
            return result
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}
