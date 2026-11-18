"""Code template generation for the editor."""

from __future__ import annotations

from algo_trainer.domain.enums import Invocation
from algo_trainer.domain.models import Problem


def render_template(problem: Problem) -> str:
    """Generate the starter Python snippet for the editor."""
    if problem.invocation is Invocation.CLASS:
        return f"class {problem.function}:\n    def __init__(self):\n        \n"

    args_str = ", ".join(f"{arg.name}: {arg.type}" for arg in problem.arguments)
    return f"def {problem.function}({args_str}) -> {problem.return_type}:\n    "
