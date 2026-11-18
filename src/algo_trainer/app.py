"""Composition root and pywebview application entry point."""

from __future__ import annotations

import multiprocessing

import webview

from algo_trainer.bridge.api import Api
from algo_trainer.config import AppConfig
from algo_trainer.execution.runner import TestRunner
from algo_trainer.problems.repository import YamlProblemRepository
from algo_trainer.stats.service import StatsService
from algo_trainer.stats.store import JsonSubmissionStore


def build_api(config: AppConfig) -> Api:
    """Wire repositories, runner, and services into the RPC facade."""
    repo = YamlProblemRepository(config.paths.problems_dir)
    repo.load()

    runner = TestRunner(config.execution)
    store = JsonSubmissionStore(config.paths.submissions_path)
    stats = StatsService(store)
    return Api(problems=repo, runner=runner, stats=stats)


def main() -> None:
    """Launch the Algo Trainer desktop window."""
    multiprocessing.freeze_support()
    config = AppConfig.load()
    api = build_api(config)

    def on_loaded() -> None:
        if webview.windows:
            webview.windows[0].evaluate_js("onPywebviewReady()")

    window = webview.create_window(
        title="Algo Trainer",
        url=str(config.paths.index_html),
        js_api=api,
        width=1400,
        height=700,
        resizable=True,
        min_size=(800, 600),
        text_select=True,
    )
    if window is None:
        raise RuntimeError("Failed to create pywebview window")

    window.events.loaded += on_loaded
    webview.start()


if __name__ == "__main__":
    main()
