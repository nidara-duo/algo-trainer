"""Test suite orchestrator with per-test and total time budgets."""

from __future__ import annotations

import time

from algo_trainer.config import ExecutionConfig
from algo_trainer.domain.matching import get_matcher
from algo_trainer.domain.models import Problem, RunReport, TestOutcome
from algo_trainer.execution.harness import ExecutionTask, serialize_value
from algo_trainer.execution.worker_pool import WorkerPool


class TestRunner:
    """Executes user code against all test cases of a `Problem`."""

    __test__ = False

    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self._config = config or ExecutionConfig()

    def run_tests(self, code: str, problem: Problem) -> RunReport:
        tests = problem.tests
        total = len(tests)
        arg_types = tuple(arg.type for arg in problem.arguments)
        matcher = get_matcher(problem.matchmode)

        outcomes: list[TestOutcome] = []
        passed_count = 0
        start_time = time.monotonic()
        timed_out_total = False

        with WorkerPool() as pool:
            for idx, test in enumerate(tests, start=1):
                elapsed = time.monotonic() - start_time
                if elapsed > self._config.total_timeout_s:
                    timed_out_total = True
                    for rem_idx in range(idx, total + 1):
                        outcomes.append(
                            TestOutcome(
                                test_num=rem_idx,
                                passed=False,
                                error="Time Limit Exceeded",
                            )
                        )
                    break

                task = ExecutionTask(
                    code=code,
                    func_name=problem.function,
                    invocation=problem.invocation.value,
                    args=test.args,
                    arg_types=arg_types,
                    return_type=problem.return_type,
                    max_stdout_bytes=self._config.max_stdout_bytes,
                )
                exec_res = pool.run_case(task, timeout_s=self._config.per_test_timeout_s)
                stdout = exec_res.get("stdout", "")
                serialized_args = serialize_value(test.args)

                if not exec_res.get("success", False):
                    got = "<timeout>" if exec_res.get("timeout") else None
                    outcomes.append(
                        TestOutcome(
                            test_num=idx,
                            passed=False,
                            args=serialized_args,
                            expected=test.expected,
                            got=got,
                            error=exec_res.get("error", "Unknown error"),
                            stdout=stdout,
                        )
                    )
                    continue

                got = exec_res.get("result")
                try:
                    passed = matcher(got, test.expected)
                    error = None
                except Exception as exc:
                    passed = False
                    error = f"Comparison error: {exc}"

                if passed:
                    passed_count += 1

                outcomes.append(
                    TestOutcome(
                        test_num=idx,
                        passed=passed,
                        args=serialized_args,
                        expected=test.expected,
                        got=got,
                        error=error,
                        stdout=stdout,
                    )
                )

        if timed_out_total:
            return RunReport(
                success=False,
                results=tuple(outcomes),
                summary=f"TLE - {passed_count}/{total} passed",
                error=(
                    f"Time Limit Exceeded: solution took more than {self._config.total_timeout_s}s"
                ),
            )

        summary = f"{passed_count}/{total} passed"
        if passed_count == total and total > 0:
            summary += " ✅"

        return RunReport(
            success=(passed_count > 0 or total == 0),
            results=tuple(outcomes),
            summary=summary,
        )
