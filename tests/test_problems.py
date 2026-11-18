"""Tests for YAML problem loading, validation, and rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from algo_trainer.config import AppConfig
from algo_trainer.domain.enums import Difficulty, Invocation, MatchMode
from algo_trainer.domain.errors import ProblemNotFoundError, ProblemValidationError
from algo_trainer.domain.models import ArgumentSpec, Problem, TestCase
from algo_trainer.problems.repository import YamlProblemRepository
from algo_trainer.rendering.examples import render_condition_with_examples
from algo_trainer.rendering.templates import render_template


def test_load_bundled_problems() -> None:
    config = AppConfig.load()
    repo = YamlProblemRepository(config.paths.problems_dir)
    repo.load()

    summaries = repo.list_summaries()
    assert len(summaries) >= 6
    assert [s.id for s in summaries] == sorted(s.id for s in summaries)

    two_sum = repo.get_by_id(1)
    assert two_sum.function == "two_sum"
    assert two_sum.invocation is Invocation.FUNCTION
    assert len(two_sum.tests) > 0


def test_missing_problem_raises() -> None:
    repo = YamlProblemRepository(Path("nonexistent"))
    repo.load()
    with pytest.raises(ProblemNotFoundError):
        repo.get_by_id(999)


def test_duplicate_problem_id_rejected(tmp_path: Path) -> None:
    content = """
id: 1
title: Sample
difficulty: Easy
function: solve
arguments:
  - name: x
    type: int
return_type: int
tests:
  - args: [1]
    output: 1
"""
    (tmp_path / "a.yaml").write_text(content, encoding="utf-8")
    (tmp_path / "b.yaml").write_text(content, encoding="utf-8")

    repo = YamlProblemRepository(tmp_path)
    with pytest.raises(ProblemValidationError, match="duplicate problem id"):
        repo.load()


def test_render_template_and_escaped_examples() -> None:
    problem = Problem(
        id=10,
        title="XSS Check",
        difficulty=Difficulty.EASY,
        matchmode=MatchMode.EXACT,
        invocation=Invocation.FUNCTION,
        function="echo",
        arguments=(ArgumentSpec(name="s", type="str"),),
        return_type="str",
        examples_count=1,
        condition="<p>Echo</p>",
        tests=(TestCase(args=("<script>alert(1)</script>",), expected="<b>ok</b>"),),
    )
    assert render_template(problem) == "def echo(s: str) -> str:\n    "
    rendered = render_condition_with_examples(problem)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert "&lt;b&gt;ok&lt;/b&gt;" in rendered
