"""Tests for the isolated code execution runner, timeouts, and codecs."""

from __future__ import annotations

import pytest

from algo_trainer.config import ExecutionConfig
from algo_trainer.domain.enums import Difficulty, Invocation, MatchMode
from algo_trainer.domain.models import ArgumentSpec, Problem, TestCase
from algo_trainer.execution.harness import ExecutionTask, _compile_solution, run_single_case
from algo_trainer.execution.runner import TestRunner


def _make_problem(
    *,
    function: str = "add",
    arguments: tuple[ArgumentSpec, ...] = (
        ArgumentSpec("a", "int"),
        ArgumentSpec("b", "int"),
    ),
    return_type: str = "int",
    invocation: Invocation = Invocation.FUNCTION,
    matchmode: MatchMode = MatchMode.EXACT,
    tests: tuple[TestCase, ...],
) -> Problem:
    return Problem(
        id=1,
        title="Test",
        difficulty=Difficulty.EASY,
        matchmode=matchmode,
        invocation=invocation,
        function=function,
        arguments=arguments,
        return_type=return_type,
        examples_count=0,
        condition="",
        tests=tests,
    )


def test_runner_passes_valid_solution_and_captures_stdout() -> None:
    problem = _make_problem(
        tests=(
            TestCase(args=(1, 2), expected=3),
            TestCase(args=(5, -2), expected=3),
        )
    )
    code = "def add(a: int, b: int) -> int:\n    print('hi', a)\n    return a + b\n"
    report = TestRunner().run_tests(code, problem)

    assert report.success is True
    assert report.summary == "2/2 passed ✅"
    assert all(r.passed for r in report.results)
    assert "hi 1" in report.results[0].stdout


def test_runner_linked_list_conversion() -> None:
    problem = _make_problem(
        function="reverse_vals",
        arguments=(ArgumentSpec("head", "Optional[ListNode]"),),
        return_type="Optional[ListNode]",
        tests=(TestCase(args=([1, 2, 3],), expected=[3, 2, 1]),),
    )
    code = """
def reverse_vals(head):
    prev = None
    curr = head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
"""
    report = TestRunner().run_tests(code, problem)
    assert report.success is True
    assert report.summary == "1/1 passed ✅"


def test_runner_class_invocation() -> None:
    problem = _make_problem(
        function="CounterBox",
        arguments=(
            ArgumentSpec("ops", "List[str]"),
            ArgumentSpec("args", "List[List[int]]"),
        ),
        return_type="List[Any]",
        invocation=Invocation.CLASS,
        tests=(
            TestCase(
                args=(["CounterBox", "inc", "get"], [[], [3], []]),
                expected=[None, None, 3],
            ),
        ),
    )
    code = """
class CounterBox:
    def __init__(self):
        self.v = 0
    def inc(self, x):
        self.v += x
    def get(self):
        return self.v
"""
    report = TestRunner().run_tests(code, problem)
    assert report.success is True
    assert report.summary == "1/1 passed ✅"


def test_runner_timeout_recovers_for_subsequent_test() -> None:
    """Regression: a hanging test must be killed and the next test must still run."""
    problem = _make_problem(
        tests=(
            TestCase(args=(1, 1), expected=2),
            TestCase(args=(2, 3), expected=5),
        )
    )
    code = """
def add(a: int, b: int) -> int:
    if a == 1:
        while True:
            pass
    return a + b
"""
    runner = TestRunner(ExecutionConfig(per_test_timeout_s=0.25, total_timeout_s=5.0))
    report = runner.run_tests(code, problem)

    assert len(report.results) == 2
    assert report.results[0].passed is False
    assert report.results[0].got == "<timeout>"
    assert "Timeout" in (report.results[0].error or "")
    assert report.results[1].passed is True
    assert report.results[1].got == 5
    assert report.summary == "1/2 passed"


def test_runner_user_redefined_list_node() -> None:
    """Regression: user code redefining `class ListNode` must still convert to list."""
    problem = _make_problem(
        function="build_list",
        arguments=(ArgumentSpec("head", "Optional[ListNode]"),),
        return_type="Optional[ListNode]",
        tests=(TestCase(args=([1, 2],), expected=[9, 1, 2]),),
    )
    code = """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def build_list(head):
    return ListNode(9, head)
"""
    report = TestRunner().run_tests(code, problem)
    assert report.success is True
    assert report.summary == "1/1 passed ✅"
    assert report.results[0].got == [9, 1, 2]


def test_runner_syntax_error_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_spawn(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("WorkerPool must not spawn on SyntaxError")

    monkeypatch.setattr("algo_trainer.execution.runner.WorkerPool", _fail_spawn)

    problem = _make_problem(
        tests=(
            TestCase(args=(1, 2), expected=3),
            TestCase(args=(3, 4), expected=7),
        )
    )
    report = TestRunner().run_tests("def add(a, b:\n    return a + b\n", problem)

    assert report.success is False
    assert report.results == ()
    assert report.summary == "0/2 passed"
    assert "SyntaxError" in (report.error or "")


def test_runner_missing_function_fails_fast() -> None:
    problem = _make_problem(
        tests=(
            TestCase(args=(1, 2), expected=3),
            TestCase(args=(3, 4), expected=7),
            TestCase(args=(5, 6), expected=11),
        )
    )
    report = TestRunner().run_tests("def wrong(a, b):\n    return a + b\n", problem)

    assert report.success is False
    assert report.results == ()
    assert report.summary == "0/3 passed"
    assert "Function 'add' not found" in (report.error or "")


def test_runner_top_level_error_fails_fast() -> None:
    problem = _make_problem(
        tests=(
            TestCase(args=(1, 2), expected=3),
            TestCase(args=(3, 4), expected=7),
            TestCase(args=(5, 6), expected=11),
        )
    )
    report = TestRunner().run_tests("1 / 0\ndef add(a, b):\n    return a + b\n", problem)

    assert report.success is False
    assert report.results == ()
    assert report.summary == "0/3 passed"
    assert "ZeroDivisionError" in (report.error or "")


def test_runner_runtime_name_error_is_not_fatal() -> None:
    problem = _make_problem(
        tests=(
            TestCase(args=(1, 2), expected=3),
            TestCase(args=(2, 3), expected=5),
        )
    )
    code = """
def add(a: int, b: int) -> int:
    if a == 1:
        return missing_var
    return a + b
"""
    report = TestRunner().run_tests(code, problem)

    assert len(report.results) == 2
    assert report.error is None
    assert report.results[0].passed is False
    assert "NameError" in (report.results[0].error or "")
    assert report.results[1].passed is True
    assert report.results[1].got == 5
    assert report.summary == "1/2 passed"


def test_harness_compile_cache_reuses_code_object() -> None:
    _compile_solution.cache_clear()
    code = "def add(a, b):\n    return a + b\n"
    task1 = ExecutionTask(
        code=code,
        func_name="add",
        invocation="function",
        args=(1, 2),
        arg_types=("int", "int"),
        return_type="int",
        max_stdout_bytes=4096,
    )
    task2 = ExecutionTask(
        code=code,
        func_name="add",
        invocation="function",
        args=(3, 4),
        arg_types=("int", "int"),
        return_type="int",
        max_stdout_bytes=4096,
    )

    res1 = run_single_case(task1)
    res2 = run_single_case(task2)

    assert res1["success"] is True and res1["result"] == 3
    assert res2["success"] is True and res2["result"] == 7
    assert _compile_solution.cache_info().hits >= 1
