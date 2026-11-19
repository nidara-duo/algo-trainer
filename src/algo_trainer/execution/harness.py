"""Single test-case execution harness."""

from __future__ import annotations

import contextlib
import functools
import io
from dataclasses import dataclass
from types import CodeType
from typing import Any

from algo_trainer.execution.prelude import (
    array_to_linked_list,
    array_to_tree,
    build_namespace,
    linked_list_to_array,
    tree_to_array,
)


@dataclass(frozen=True, slots=True)
class ExecutionTask:
    """Payload sent from the parent process to the worker process."""

    code: str
    func_name: str
    invocation: str  # "function" | "class"
    args: tuple[Any, ...]
    arg_types: tuple[str, ...]
    return_type: str
    max_stdout_bytes: int


def _convert_input_args(args: tuple[Any, ...], arg_types: tuple[str, ...]) -> list[Any]:
    converted: list[Any] = []
    for idx, arg in enumerate(args):
        arg_type = arg_types[idx] if idx < len(arg_types) else ""
        if arg_type in ("Optional[ListNode]", "ListNode") and isinstance(arg, list):
            converted.append(array_to_linked_list(arg))
        elif arg_type in ("Optional[TreeNode]", "TreeNode") and isinstance(arg, list):
            converted.append(array_to_tree(arg))
        else:
            converted.append(arg)
    return converted


def _is_list_node(obj: Any) -> bool:
    return hasattr(obj, "val") and hasattr(obj, "next")


def _is_tree_node(obj: Any) -> bool:
    return hasattr(obj, "val") and hasattr(obj, "left") and hasattr(obj, "right")


def _convert_output(result: Any, return_type: str) -> Any:
    if "ListNode" in return_type:
        if result is None:
            return []
        if _is_list_node(result):
            return linked_list_to_array(result)

    if "TreeNode" in return_type:
        if result is None:
            return []
        if _is_tree_node(result):
            return tree_to_array(result)
        if isinstance(result, list) and any(_is_tree_node(node) for node in result):
            return [tree_to_array(node) if node is not None else None for node in result]

    return result


def serialize_value(value: Any) -> Any:
    """Convert arbitrary Python values to JSON-safe structures."""
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): serialize_value(v) for k, v in value.items()}
    if hasattr(value, "__dict__"):
        return {type(value).__name__: serialize_value(value.__dict__)}
    return repr(value)


def _invoke_class(namespace: dict[str, Any], args: tuple[Any, ...]) -> list[Any]:
    if len(args) != 2 or not isinstance(args[0], list) or not isinstance(args[1], list):
        raise ValueError("Class invocation expects [methods, method_args]")

    class_name = args[0][0]
    methods = args[0][1:]
    method_args_list = args[1][1:]

    if class_name not in namespace:
        raise NameError(f"Class '{class_name}' not found")

    cls = namespace[class_name]
    init_args = args[1][0] if args[1] else []
    instance = cls(*init_args) if isinstance(init_args, list) and init_args else cls()
    results: list[Any] = [None]

    for method_name, method_arg in zip(methods, method_args_list, strict=True):
        if not hasattr(instance, method_name):
            raise AttributeError(f"Method '{method_name}' not found")
        method = getattr(instance, method_name)
        if isinstance(method_arg, list):
            results.append(method(*method_arg))
        else:
            results.append(method(method_arg))
    return results


def _truncate_stdout(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n... [stdout truncated]"


@functools.lru_cache(maxsize=16)
def _compile_solution(code: str) -> CodeType:
    return compile(code, "<solution>", "exec")


def run_single_case(task: ExecutionTask) -> dict[str, Any]:
    """Compile and execute user code for a single test case."""
    namespace = build_namespace()
    stdout_buf = io.StringIO()

    try:
        compiled = _compile_solution(task.code)
        with contextlib.redirect_stdout(stdout_buf):
            exec(compiled, namespace)
    except Exception as exc:
        return {
            "success": False,
            "fatal": True,
            "result": None,
            "error": f"{type(exc).__name__}: {exc}",
            "stdout": _truncate_stdout(stdout_buf.getvalue(), task.max_stdout_bytes),
        }

    if task.invocation == "class":
        if (
            len(task.args) != 2
            or not isinstance(task.args[0], list)
            or not isinstance(task.args[1], list)
            or not task.args[0]
        ):
            return {
                "success": False,
                "fatal": True,
                "result": None,
                "error": "ValueError: Class invocation expects [methods, method_args]",
                "stdout": _truncate_stdout(stdout_buf.getvalue(), task.max_stdout_bytes),
            }
        class_name = task.args[0][0]
        if class_name not in namespace:
            return {
                "success": False,
                "fatal": True,
                "result": None,
                "error": f"NameError: Class '{class_name}' not found",
                "stdout": _truncate_stdout(stdout_buf.getvalue(), task.max_stdout_bytes),
            }
    elif task.func_name not in namespace:
        return {
            "success": False,
            "fatal": True,
            "result": None,
            "error": f"NameError: Function '{task.func_name}' not found",
            "stdout": _truncate_stdout(stdout_buf.getvalue(), task.max_stdout_bytes),
        }

    try:
        with contextlib.redirect_stdout(stdout_buf):
            if task.invocation == "class":
                raw_result: Any = _invoke_class(namespace, task.args)
            else:
                fn = namespace[task.func_name]
                converted_args = _convert_input_args(task.args, task.arg_types)
                raw_result = fn(*converted_args)
                if task.return_type == "None" and converted_args:
                    raw_result = converted_args[0]
                raw_result = _convert_output(raw_result, task.return_type)

        return {
            "success": True,
            "result": serialize_value(raw_result),
            "error": None,
            "stdout": _truncate_stdout(stdout_buf.getvalue(), task.max_stdout_bytes),
        }
    except Exception as exc:
        return {
            "success": False,
            "fatal": False,
            "result": None,
            "error": f"{type(exc).__name__}: {exc}",
            "stdout": _truncate_stdout(stdout_buf.getvalue(), task.max_stdout_bytes),
        }
