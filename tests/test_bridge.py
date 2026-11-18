"""Integration tests for the pywebview RPC bridge contract."""

from __future__ import annotations

from pathlib import Path

from algo_trainer.app import build_api
from algo_trainer.config import AppConfig, AppPaths, ExecutionConfig


def test_bridge_contract(tmp_path: Path) -> None:
    root = AppPaths.resolve().web_root
    config = AppConfig(
        paths=AppPaths(
            web_root=root,
            problems_dir=root / "data" / "problems",
            state_dir=tmp_path,
        ),
        execution=ExecutionConfig(),
    )
    api = build_api(config)

    problems_res = api.get_problems()
    assert "problems" in problems_res
    assert len(problems_res["problems"]) >= 6

    missing = api.get_problem(999999)
    assert "error" in missing
    assert "traceback" not in missing

    p1 = api.get_problem("1")  # type: ignore[arg-type]
    assert p1["problem"]["id"] == 1

    code = """
def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []
"""
    run_res = api.run_tests(1, code)
    assert run_res["success"] is True
    assert "✅" in run_res["summary"]
