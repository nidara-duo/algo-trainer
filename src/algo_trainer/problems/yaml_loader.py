"""YAML problem parser and schema validator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from algo_trainer.domain.enums import Difficulty, Invocation, MatchMode
from algo_trainer.domain.errors import ProblemValidationError
from algo_trainer.domain.models import ArgumentSpec, Problem, TestCase


def _infer_invocation(tests: tuple[TestCase, ...]) -> Invocation:
    """Fallback heuristic for legacy YAML files without explicit `invocation`."""
    if not tests:
        return Invocation.FUNCTION
    args = tests[0].args
    if (
        len(args) == 2
        and isinstance(args[0], list)
        and isinstance(args[1], list)
        and len(args[0]) > 1
        and len(args[0]) == len(args[1])
        and isinstance(args[0][0], str)
        and args[0][0][:1].isupper()
    ):
        return Invocation.CLASS
    return Invocation.FUNCTION


def _parse_enum[E](enum_cls: type[E], raw: Any, field_name: str, source: Path) -> E:
    try:
        return enum_cls(raw)  # type: ignore[call-arg]
    except ValueError as exc:
        raise ProblemValidationError(source, f"invalid {field_name} value: {raw!r}") from exc


def load_problem_yaml(path: Path) -> Problem:
    """Load and validate a single `.yaml` problem file into a `Problem`."""
    try:
        raw_text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text)
    except (OSError, yaml.YAMLError) as exc:
        raise ProblemValidationError(path, f"failed to read YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ProblemValidationError(path, "root YAML node must be a mapping")

    if "id" not in data or isinstance(data["id"], bool) or not isinstance(data["id"], int):
        raise ProblemValidationError(path, "missing or non-integer 'id'")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ProblemValidationError(path, "missing or empty 'title'")

    difficulty = _parse_enum(Difficulty, data.get("difficulty"), "difficulty", path)
    matchmode = _parse_enum(
        MatchMode, data.get("matchmode") or MatchMode.EXACT.value, "matchmode", path
    )

    function = data.get("function")
    if not isinstance(function, str) or not function.strip():
        raise ProblemValidationError(path, "missing or empty 'function'")

    raw_args = data.get("arguments")
    if raw_args is None:
        raw_args = []
    if not isinstance(raw_args, list):
        raise ProblemValidationError(path, "'arguments' must be a list")

    arguments: list[ArgumentSpec] = []
    for idx, arg in enumerate(raw_args):
        if (
            not isinstance(arg, dict)
            or not isinstance(arg.get("name"), str)
            or not isinstance(arg.get("type"), str)
        ):
            raise ProblemValidationError(path, f"invalid argument at index {idx}")
        arguments.append(ArgumentSpec(name=arg["name"], type=arg["type"]))

    return_type = data.get("return_type")
    if not isinstance(return_type, str) or not return_type.strip():
        raise ProblemValidationError(path, "missing or empty 'return_type'")

    raw_tests = data.get("tests")
    if not isinstance(raw_tests, list) or not raw_tests:
        raise ProblemValidationError(path, "'tests' must be a non-empty list")

    tests: list[TestCase] = []
    for idx, test in enumerate(raw_tests):
        if not isinstance(test, dict) or "args" not in test or "output" not in test:
            raise ProblemValidationError(path, f"test #{idx} must have 'args' and 'output'")
        test_args = test["args"]
        if not isinstance(test_args, list):
            raise ProblemValidationError(path, f"test #{idx} 'args' must be a list")
        tests.append(TestCase(args=tuple(test_args), expected=test["output"]))

    tests_tuple = tuple(tests)
    raw_invocation = data.get("invocation")
    if raw_invocation is not None:
        invocation = _parse_enum(Invocation, raw_invocation, "invocation", path)
    else:
        invocation = _infer_invocation(tests_tuple)

    examples_raw = data.get("examples", 2)
    if isinstance(examples_raw, bool) or not isinstance(examples_raw, int) or examples_raw < 0:
        raise ProblemValidationError(path, "'examples' must be a non-negative integer")

    condition = data.get("condition")
    if condition is None:
        condition = ""
    if not isinstance(condition, str):
        raise ProblemValidationError(path, "'condition' must be a string")

    solution = data.get("solution")
    if solution is not None and not isinstance(solution, str):
        raise ProblemValidationError(path, "'solution' must be a string if provided")

    return Problem(
        id=data["id"],
        title=title,
        difficulty=difficulty,
        matchmode=matchmode,
        invocation=invocation,
        function=function,
        arguments=tuple(arguments),
        return_type=return_type,
        examples_count=examples_raw,
        condition=condition,
        tests=tests_tuple,
        solution=solution,
    )
