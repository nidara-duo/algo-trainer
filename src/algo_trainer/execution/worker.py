"""Isolated child-process worker loop (no UI or app-level imports)."""

from __future__ import annotations

from multiprocessing.connection import Connection

from algo_trainer.execution.harness import ExecutionTask, run_single_case


def worker_loop(conn: Connection) -> None:
    """Receive ExecutionTask objects over `conn`, run them, and send back results."""
    try:
        while True:
            try:
                task: ExecutionTask | None = conn.recv()
            except EOFError:
                break
            if task is None:
                break
            outcome = run_single_case(task)
            conn.send(outcome)
    finally:
        conn.close()
