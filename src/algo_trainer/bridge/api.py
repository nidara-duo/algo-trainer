"""pywebview JavaScript-to-Python RPC bridge."""

from __future__ import annotations

import functools
import traceback
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from algo_trainer.domain.errors import ProblemNotFoundError
from algo_trainer.domain.models import Problem, RunReport
from algo_trainer.execution.runner import TestRunner
from algo_trainer.problems.repository import ProblemRepository
from algo_trainer.rendering.examples import render_condition_with_examples
from algo_trainer.rendering.templates import render_template
from algo_trainer.stats.service import StatsService


def _rpc(fn: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Convert domain/unexpected exceptions into uniform JSON error payloads."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return fn(*args, **kwargs)
        except ProblemNotFoundError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            return {"error": str(exc), "traceback": traceback.format_exc()}

    return wrapper


def _serialize_problem(problem: Problem) -> dict[str, Any]:
    return {
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty.value,
        "matchmode": problem.matchmode.value,
        "invocation": problem.invocation.value,
        "function": problem.function,
        "arguments": [{"name": a.name, "type": a.type} for a in problem.arguments],
        "return_type": problem.return_type,
        "condition": render_condition_with_examples(problem),
        "template": render_template(problem),
        "tests": [{"args": list(t.args), "expected": t.expected} for t in problem.tests],
        "author_solution": problem.solution,
    }


def _serialize_report(report: RunReport) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": report.success,
        "results": [asdict(outcome) for outcome in report.results],
        "summary": report.summary,
    }
    if report.error is not None:
        payload["error"] = report.error
    return payload


class Api:
    """Thin facade exposed to pywebview's `window.pywebview.api`."""

    def __init__(
        self,
        problems: ProblemRepository,
        runner: TestRunner,
        stats: StatsService,
    ) -> None:
        self._problems = problems
        self._runner = runner
        self._stats = stats

    @_rpc
    def get_problems(self) -> dict[str, Any]:
        summaries = self._problems.list_summaries()
        return {
            "problems": [
                {"id": s.id, "title": s.title, "difficulty": s.difficulty.value} for s in summaries
            ]
        }

    @_rpc
    def get_problem(self, problem_id: int) -> dict[str, Any]:
        problem = self._problems.get_by_id(int(problem_id))
        return {"problem": _serialize_problem(problem)}

    @_rpc
    def run_tests(self, problem_id: int, code: str) -> dict[str, Any]:
        problem = self._problems.get_by_id(int(problem_id))
        report = self._runner.run_tests(code, problem)
        return _serialize_report(report)

    @_rpc
    def start_problem_session(self, problem_id: int) -> dict[str, Any]:
        pid = int(problem_id)
        self._stats.start_problem(pid)
        return {"success": True, "problem_id": pid}

    @_rpc
    def record_submission(
        self,
        problem_id: int,
        tests_passed: int,
        tests_total: int,
        code: str,
        time_spent_seconds: int | None = None,
    ) -> dict[str, Any]:
        submission = self._stats.record_submission(
            problem_id=int(problem_id),
            tests_passed=tests_passed,
            tests_total=tests_total,
            code=code,
            time_spent_seconds=time_spent_seconds,
        )
        return {"success": True, "submission": asdict(submission)}

    @_rpc
    def get_statistics(self) -> dict[str, Any]:
        return self._stats.get_statistics()

    @_rpc
    def get_problem_statistics(self, problem_id: int) -> dict[str, Any]:
        return self._stats.get_problem_stats(int(problem_id))

    @_rpc
    def reset_statistics(self) -> dict[str, Any]:
        return self._stats.reset_statistics()
