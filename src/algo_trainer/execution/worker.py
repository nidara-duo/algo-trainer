"""Isolated child-process worker loop (no UI or app-level imports)."""

from __future__ import annotations

from typing import Any, Protocol

from algo_trainer.execution.harness import ExecutionTask, run_single_case

WORKER_READY = "ready"


class PipeConn(Protocol):
    def send(self, obj: Any) -> None: ...
    def recv(self) -> Any: ...
    def poll(self, timeout: float | None = ...) -> bool: ...
    def close(self) -> None: ...


def worker_loop(conn: PipeConn) -> None:
    """Receive ExecutionTask objects over `conn`, run them, and send back results."""
    try:
        conn.send(WORKER_READY)
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
