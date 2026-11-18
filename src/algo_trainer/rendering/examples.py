"""HTML rendering for problem conditions and examples."""

from __future__ import annotations

import html

from algo_trainer.domain.models import Problem

_EXAMPLE_TEMPLATE = """
<p><strong>Example {num}:</strong></p>
<div class="example-block">
  <div class="example-section">
    <div class="example-label">Input:</div>
    <div class="example-content">{input_html}</div>
  </div>
  <div class="example-section">
    <div class="example-label">Output:</div>
    <div class="example-content"><code>{output_html}</code></div>
  </div>
</div>"""


def render_condition_with_examples(problem: Problem) -> str:
    """Append escaped HTML example blocks to the problem condition."""
    if problem.examples_count <= 0 or not problem.tests:
        return problem.condition

    arg_names = [arg.name for arg in problem.arguments]
    count = min(problem.examples_count, len(problem.tests))

    blocks: list[str] = [problem.condition, "\n\n<h3>Examples</h3>"]
    for idx in range(count):
        test = problem.tests[idx]
        input_lines = [
            f"{html.escape(name)} = {html.escape(repr(value))}"
            for name, value in zip(arg_names, test.args, strict=False)
        ]
        blocks.append(
            _EXAMPLE_TEMPLATE.format(
                num=idx + 1,
                input_html="\n".join(input_lines),
                output_html=html.escape(repr(test.expected)),
            )
        )

    return "".join(blocks)
