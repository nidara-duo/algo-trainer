"""CLI validator for bundled problem YAML files (`algo-trainer-check`)."""

from __future__ import annotations

import sys

from algo_trainer.config import AppConfig
from algo_trainer.domain.enums import Invocation
from algo_trainer.domain.errors import ProblemValidationError
from algo_trainer.execution.runner import TestRunner
from algo_trainer.problems.repository import YamlProblemRepository
from algo_trainer.rendering.examples import render_condition_with_examples
from algo_trainer.rendering.templates import render_template


def main() -> int:
    """Validate all YAML problems and run any embedded solutions."""
    config = AppConfig.load()
    repo = YamlProblemRepository(config.paths.problems_dir)

    try:
        repo.load()
    except ProblemValidationError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    problems = repo.list_all()
    if not problems:
        print(f"[WARN] No problems found in {config.paths.problems_dir}")
        return 0

    runner = TestRunner(config.execution)
    failures = 0

    for problem in problems:
        if problem.invocation is Invocation.FUNCTION:
            expected_arity = len(problem.arguments)
            for idx, test in enumerate(problem.tests, start=1):
                if len(test.args) != expected_arity:
                    print(
                        f"[FAIL] Problem {problem.id} ({problem.title}) test #{idx}: "
                        f"expected {expected_arity} args, got {len(test.args)}",
                        file=sys.stderr,
                    )
                    failures += 1
                    break

        render_template(problem)
        render_condition_with_examples(problem)

        if problem.solution:
            report = runner.run_tests(problem.solution, problem)
            if not report.success or "❌" in report.summary or "✅" not in report.summary:
                print(
                    f"[FAIL] Problem {problem.id} ({problem.title}) solution: {report.summary}",
                    file=sys.stderr,
                )
                failures += 1
                continue

        print(f"[OK] #{problem.id} {problem.title} ({len(problem.tests)} tests)")

    print(f"Checked {len(problems)} problems, {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
