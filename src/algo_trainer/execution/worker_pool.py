"""Warm single-worker process pool with hard kill and Pipe recreation on timeout."""

from __future__ import annotations

import multiprocessing
from multiprocessing.context import SpawnProcess
from typing import Any, Protocol

from algo_trainer.execution.harness import ExecutionTask
from algo_trainer.execution.worker import worker_loop


class _PipeConn(Protocol):
    def send(self, obj: Any) -> None: ...
    def recv(self) -> Any: ...
    def poll(self, timeout: float | None = ...) -> bool: ...
    def close(self) -> None: ...


class WorkerPool:
    """Manages a single warm spawned worker process for sequential test execution."""

    def __init__(self) -> None:
        self._ctx = multiprocessing.get_context("spawn")
        self._process: SpawnProcess | None = None
        self._parent_conn: _PipeConn | None = None

    def __enter__(self) -> WorkerPool:
        self._spawn()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _spawn(self) -> None:
        parent_conn, child_conn = self._ctx.Pipe(duplex=True)
        process = self._ctx.Process(target=worker_loop, args=(child_conn,), daemon=True)
        process.start()
        # Close child end in parent so EOF propagates cleanly if worker exits.
        child_conn.close()
        self._parent_conn = parent_conn
        self._process = process

    def _kill_and_reset(self) -> None:
        if self._process is not None:
            if self._process.is_alive():
                self._process.kill()
            self._process.join(timeout=0.5)
            self._process = None
        if self._parent_conn is not None:
            self._parent_conn.close()
            self._parent_conn = None

    def run_case(self, task: ExecutionTask, timeout_s: float) -> dict[str, Any]:
        """Run `task` in the warm worker, killing and respawning on timeout or crash."""
        if self._process is None or not self._process.is_alive() or self._parent_conn is None:
            self._kill_and_reset()
            self._spawn()

        assert self._parent_conn is not None
        try:
            self._parent_conn.send(task)
            if not self._parent_conn.poll(timeout_s):
                self._kill_and_reset()
                return {
                    "success": False,
                    "timeout": True,
                    "result": None,
                    "error": f"Timeout: test exceeded {timeout_s}s",
                    "stdout": "",
                }
            result: dict[str, Any] = self._parent_conn.recv()
            return result
        except (EOFError, BrokenPipeError, OSError) as exc:
            exit_code = self._process.exitcode if self._process is not None else None
            self._kill_and_reset()
            reason = (
                f"exit code {exit_code}"
                if exit_code is not None
                else (str(exc) or type(exc).__name__)
            )
            return {
                "success": False,
                "timeout": False,
                "result": None,
                "error": f"Worker crashed ({reason})",
                "stdout": "",
            }

    def close(self) -> None:
        """Gracefully shut down the worker process and close its pipe."""
        if self._parent_conn is not None and self._process is not None and self._process.is_alive():
            try:
                self._parent_conn.send(None)
                self._process.join(timeout=0.5)
            except (BrokenPipeError, OSError):
                pass
        self._kill_and_reset()
