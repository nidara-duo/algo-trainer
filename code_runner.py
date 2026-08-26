"""
Code Runner - executes user code and runs tests in an isolated namespace.

Features:
- Caches compiled AUTO_IMPORTS to avoid recompilation
- Uses isolated namespace per execution
- Uses multiprocessing to kill infinite loops
- Strict per-test timeout (0.5s)
- Total time limit (3s) for all tests combined
- Worker process reuse to reduce spawn overhead
"""

import ast
import io
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
import sys
import time
import traceback
from typing import Any


AUTO_IMPORTS = """from typing import List, Optional, Tuple, Dict, Set, Any
from collections import defaultdict, Counter, deque
import heapq
import math

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def array_to_linked_list(arr):
    if not arr:
        return None
    head = ListNode(arr[0])
    current = head
    for val in arr[1:]:
        current.next = ListNode(val)
        current = current.next
    return head

def linked_list_to_array(head):
    result = []
    current = head
    while current:
        result.append(current.val)
        current = current.next
    return result

def array_to_tree(arr):
    if not arr:
        return None
    root = TreeNode(arr[0])
    queue = [root]
    i = 1
    while queue and i < len(arr):
        node = queue.pop(0)
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root

def tree_to_array(root):
    if not root:
        return []
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    while result and result[-1] is None:
        result.pop()
    return result
"""

_SUBPROCESS_NAMESPACE = None


def _run_test_direct(code_str, func_name, args, return_type=None, func_args_json="[]"):
    """
    Synchronous version of _run_test_in_process that returns result directly.
    Used with ProcessPoolExecutor for worker reuse.
    """
    global _SUBPROCESS_NAMESPACE
    import json

    try:
        func_args = json.loads(func_args_json)

        if _SUBPROCESS_NAMESPACE is None:
            _SUBPROCESS_NAMESPACE = {}
            exec(AUTO_IMPORTS, _SUBPROCESS_NAMESPACE)

        namespace = _SUBPROCESS_NAMESPACE.copy()

        array_to_ll = namespace['array_to_linked_list']
        ll_to_array = namespace['linked_list_to_array']
        array_to_tree = namespace['array_to_tree']
        tree_to_array = namespace['tree_to_array']

        converted_args = []
        if func_args:
            for arg, arg_def in zip(args, func_args):
                arg_type = arg_def.get("type", "")
                if arg_type in ("Optional[ListNode]", "ListNode"):
                    if isinstance(arg, list):
                        converted_args.append(array_to_ll(arg))
                    else:
                        converted_args.append(arg)
                elif arg_type in ("Optional[TreeNode]", "TreeNode"):
                    if isinstance(arg, list):
                        converted_args.append(array_to_tree(arg))
                    else:
                        converted_args.append(arg)
                else:
                    converted_args.append(arg)
        else:
            converted_args = list(args)

        exec(code_str, namespace)
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}

    try:
        is_class_problem = (
            len(args) == 2 and
            isinstance(args[0], list) and
            isinstance(args[1], list) and
            len(args[0]) > 1 and
            len(args[0]) == len(args[1]) and
            isinstance(args[0][0], str) and
            args[0][0][0].isupper()
        )

        if is_class_problem:
            class_name = args[0][0]
            methods = args[0][1:]
            method_args = args[1]

            if class_name not in namespace:
                return {"success": False, "error": f"Class '{class_name}' not found in {list(namespace.keys())}"}

            cls = namespace[class_name]
            instance = cls()
            results = [None]

            for method_name, method_arg in zip(methods, method_args[1:]):
                if not hasattr(instance, method_name):
                    return {"success": False, "error": f"Method '{method_name}' not found"}
                method = getattr(instance, method_name)
                try:
                    actual_arg = method_arg[0] if isinstance(method_arg, list) and len(method_arg) == 1 else method_arg
                    result = method(actual_arg) if method_arg != [] else method()
                    results.append(result)
                except Exception as e:
                    return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}

            return {"success": True, "result": results}

        if func_name not in namespace:
            return {"success": False, "error": f"Function '{func_name}' not found"}

        fn = namespace[func_name]
        result = fn(*converted_args)

        if return_type == "None" and converted_args and len(converted_args) > 0:
            result = converted_args[0]

        if return_type and "ListNode" in return_type:
            if result is None:
                result = []
            elif isinstance(result, namespace['ListNode']):
                result = ll_to_array(result)

        if return_type and "TreeNode" in return_type:
            if result is None:
                result = []
            elif isinstance(result, namespace['TreeNode']):
                result = tree_to_array(result)
            elif isinstance(result, list):
                TreeNodeClass = namespace['TreeNode']
                if result and isinstance(result[0], TreeNodeClass):
                    result = [tree_to_array(node) if node is not None else None for node in result]

        if hasattr(result, '__class__') and result.__class__.__name__ in ('RandomizedSet',):
            result = f"<{result.__class__.__name__} instance>"

        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


def _run_test_in_process(code_str, func_name, args, result_queue, return_type=None, func_args_json="[]"):
    """
    Target function for multiprocessing.Process (legacy, kept for backward compatibility).
    """
    global _SUBPROCESS_NAMESPACE
    import json

    try:
        func_args = json.loads(func_args_json)

        if _SUBPROCESS_NAMESPACE is None:
            _SUBPROCESS_NAMESPACE = {}
            exec(AUTO_IMPORTS, _SUBPROCESS_NAMESPACE)

        namespace = _SUBPROCESS_NAMESPACE.copy()

        array_to_ll = namespace['array_to_linked_list']
        ll_to_array = namespace['linked_list_to_array']
        array_to_tree = namespace['array_to_tree']
        tree_to_array = namespace['tree_to_array']

        converted_args = []
        if func_args:
            for arg, arg_def in zip(args, func_args):
                arg_type = arg_def.get("type", "")
                if arg_type in ("Optional[ListNode]", "ListNode"):
                    if isinstance(arg, list):
                        converted_args.append(array_to_ll(arg))
                    else:
                        converted_args.append(arg)
                elif arg_type in ("Optional[TreeNode]", "TreeNode"):
                    if isinstance(arg, list):
                        converted_args.append(array_to_tree(arg))
                    else:
                        converted_args.append(arg)
                else:
                    converted_args.append(arg)
        else:
            converted_args = list(args)

        exec(code_str, namespace)
    except Exception as e:
        result_queue.put({"success": False, "error": f"{type(e).__name__}: {str(e)}"})
        return

    try:
        is_class_problem = (
            len(args) == 2 and
            isinstance(args[0], list) and
            isinstance(args[1], list) and
            len(args[0]) > 1 and
            len(args[0]) == len(args[1]) and
            isinstance(args[0][0], str) and
            args[0][0][0].isupper()
        )

        if is_class_problem:
            class_name = args[0][0]
            methods = args[0][1:]
            method_args = args[1]

            if class_name not in namespace:
                result_queue.put({"success": False, "error": f"Class '{class_name}' not found in {list(namespace.keys())}"})
                return

            cls = namespace[class_name]
            instance = cls()
            results = [None]

            for method_name, method_arg in zip(methods, method_args[1:]):
                if not hasattr(instance, method_name):
                    result_queue.put({"success": False, "error": f"Method '{method_name}' not found" })
                    return
                method = getattr(instance, method_name)
                try:
                    actual_arg = method_arg[0] if isinstance(method_arg, list) and len(method_arg) == 1 else method_arg
                    result = method(actual_arg) if method_arg != [] else method()
                    results.append(result)
                except Exception as e:
                    result_queue.put({"success": False, "error": f"{type(e).__name__}: {str(e)}"})
                    return

            result_queue.put({"success": True, "result": results})
            return

        if func_name not in namespace:
            result_queue.put({"success": False, "error": f"Function '{func_name}' not found"})
            return

        fn = namespace[func_name]
        converted_args = list(args)

        if func_args and isinstance(func_args, list) and len(func_args) == len(converted_args):
            for i, arg_def in enumerate(func_args):
                arg_type = arg_def.get("type", "")
                arg_value = converted_args[i]

                if "TreeNode" in arg_type and isinstance(arg_value, list):
                    converted_args[i] = array_to_tree(arg_value)
                elif "ListNode" in arg_type and isinstance(arg_value, list):
                    converted_args[i] = array_to_ll(arg_value)

        result = fn(*converted_args)

        if return_type == "None" and converted_args and len(converted_args) > 0:
            result = converted_args[0]

        if return_type and "ListNode" in return_type:
            if result is None:
                result = []
            elif isinstance(result, namespace['ListNode']):
                result = ll_to_array(result)

        if return_type and "TreeNode" in return_type:
            if result is None:
                result = []
            elif isinstance(result, namespace['TreeNode']):
                result = tree_to_array(result)
            elif isinstance(result, list):
                TreeNodeClass = namespace['TreeNode']
                if result and isinstance(result[0], TreeNodeClass):
                    result = [tree_to_array(node) if node is not None else None for node in result]

        if hasattr(result, '__class__') and result.__class__.__name__ in ('RandomizedSet',):
            result = f"<{result.__class__.__name__} instance>"

        result_queue.put({"success": True, "result": result})

    except Exception as e:
        result_queue.put({"success": False, "error": f"{type(e).__name__}: {str(e)}"})


class CodeRunner:
    """Runs user code against test cases with timeout protection."""

    TOTAL_TIME_LIMIT = 3
    PER_TEST_TIME_LIMIT = 0.5

    _compiled_imports_cache = None
    _import_namespace_cache = None

    def __init__(self):
        """Initialize CodeRunner and pre-compile imports."""
        if CodeRunner._compiled_imports_cache is None:
            CodeRunner._compiled_imports_cache = compile(
                AUTO_IMPORTS, '<auto_imports>', 'exec'
            )
        if CodeRunner._import_namespace_cache is None:
            base_namespace = {}
            exec(CodeRunner._compiled_imports_cache, base_namespace)
            CodeRunner._import_namespace_cache = base_namespace

    def run_tests(self, code: str, problem: dict) -> dict:
        """
        Run user code against all test cases sequentially.
        """
        results = {
            "success": True,
            "results": [],
            "summary": "",
        }

        func_name = problem.get("function", "")
        matchmode = problem.get("matchmode", "exact")
        tests = problem.get("tests", [])
        total = len(tests)

        passed_count = 0
        start_time = time.time()
        elapsed = 0

        with ProcessPoolExecutor(max_workers=1) as executor:
            for i, test in enumerate(tests, start=1):
                elapsed = time.time() - start_time
                if elapsed > self.TOTAL_TIME_LIMIT:
                    results["success"] = False
                    results["error"] = f"Time Limit Exceeded: solution took more than {self.TOTAL_TIME_LIMIT}s"
                    results["summary"] = f"TLE - {passed_count}/{total} passed"
                    for j in range(i, total + 1):
                        results["results"].append({
                            "test_num": j,
                            "passed": False,
                            "error": "Time Limit Exceeded",
                        })
                    break

                test_result = self._run_single_test_with_executor(
                    executor, code, func_name, test["args"], test["expected"],
                    matchmode, i, problem.get("return_type", ""), problem.get("arguments", [])
                )
                results["results"].append(test_result)

                if test_result["passed"]:
                    passed_count += 1

        if elapsed <= self.TOTAL_TIME_LIMIT:
            results["summary"] = f"{passed_count}/{total} passed"
            if passed_count == total and total > 0:
                results["summary"] += " ✅"
            elif passed_count == 0:
                results["success"] = False

        return results

    def _run_single_test_with_executor(self, executor: ProcessPoolExecutor, code: str, func_name: str, args: Any, expected: Any, matchmode: str, test_num: int, return_type: str = "", func_args: list | None = None) -> dict:
        """Run a single test case using ProcessPoolExecutor with strict timeout."""
        result = {
            "test_num": test_num,
            "passed": False,
            "args": self._serialize_args(args),
            "expected": expected,
            "got": None,
            "error": None,
            "stdout": "",
        }

        if isinstance(args, (list, tuple)):
            if len(args) == 2 and isinstance(args[0], (list, tuple, dict)) and not isinstance(args[0], str):
                fn_args = list(args)
            else:
                fn_args = list(args) if isinstance(args, tuple) else args
        else:
            fn_args = [args]

        import json
        func_args_json = json.dumps(func_args) if func_args else "[]"

        future = executor.submit(
            _run_test_direct,
            code, func_name, fn_args, return_type, func_args_json
        )

        try:
            exec_result = future.result(timeout=self.PER_TEST_TIME_LIMIT)

            if isinstance(exec_result, dict) and not exec_result.get("success", True):
                result["error"] = exec_result.get("error", "Unknown error")
                return result

            got = exec_result.get("result") if isinstance(exec_result, dict) else None
            result["got"] = got

            try:
                if matchmode == "exact":
                    result["passed"] = self._compare_exact(got, expected)
                elif matchmode == "sorted":
                    result["passed"] = self._compare_sorted(got, expected)
                elif matchmode == "approx":
                    result["passed"] = self._compare_approx(got, expected)
                else:
                    result["passed"] = self._compare_exact(got, expected)
            except Exception as e:
                result["error"] = f"Comparison error: {str(e)}"
                result["passed"] = False

        except FuturesTimeoutError:
            result["error"] = f"Timeout: test exceeded {self.PER_TEST_TIME_LIMIT}s"
            result["got"] = "<timeout>"
            executor.shutdown(wait=False, cancel_futures=True)

        return result

    def _run_single_test(self, code: str, func_name: str, args: Any, expected: Any, matchmode: str, test_num: int, return_type: str = "", func_args: list | None = None) -> dict:
        """Run a single test case in a separate process with strict timeout."""
        result = {
            "test_num": test_num,
            "passed": False,
            "args": self._serialize_args(args),
            "expected": expected,
            "got": None,
            "error": None,
            "stdout": "",
        }

        if isinstance(args, (list, tuple)):
            if len(args) == 2 and isinstance(args[0], (list, tuple, dict)) and not isinstance(args[0], str):
                fn_args = list(args)
            else:
                fn_args = list(args) if isinstance(args, tuple) else args
        else:
            fn_args = [args]

        import json
        func_args_json = json.dumps(func_args) if func_args else "[]"

        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=_run_test_in_process,
            args=(code, func_name, fn_args, result_queue, return_type, func_args_json)
        )
        process.start()
        process.join(timeout=self.PER_TEST_TIME_LIMIT)

        if process.is_alive():
            process.kill()
            process.join(timeout=0.1)
            result["error"] = f"Timeout: test exceeded {self.PER_TEST_TIME_LIMIT}s"
            result["got"] = "<timeout>"
            return result

        if not result_queue.empty():
            exec_result = result_queue.get()
            if not exec_result["success"]:
                result["error"] = exec_result["error"]
                return result

            got = exec_result["result"]
            result["got"] = got

            try:
                if matchmode == "exact":
                    result["passed"] = self._compare_exact(got, expected)
                elif matchmode == "sorted":
                    result["passed"] = self._compare_sorted(got, expected)
                elif matchmode == "approx":
                    result["passed"] = self._compare_approx(got, expected)
                else:
                    result["passed"] = self._compare_exact(got, expected)
            except Exception as e:
                result["error"] = f"Comparison error: {str(e)}"
                result["passed"] = False
        else:
            result["error"] = "No result from test"
            result["passed"] = False

        return result

    def _serialize_args(self, args: Any) -> Any:
        """Serialize args for JSON output efficiently."""
        if args is None:
            return None
        if type(args) in (int, float, str, bool):
            return args
        if type(args) is list:
            return [self._serialize_args(a) for a in args]
        if type(args) is dict:
            return {k: self._serialize_args(v) for k, v in args.items()}
        if type(args) is tuple:
            return [self._serialize_args(a) for a in args]

        if hasattr(args, "__dict__"):
            return {type(args).__name__: self._serialize_args(args.__dict__)}
        return str(args)

    def _compare_exact(self, got: Any, expected: Any) -> bool:
        """Compare values exactly, with fast paths for primitives."""
        if got == expected:
            return True

        if got is None and expected is None:
            return True
        if got is None and expected == [None, None]:
            return True

        if isinstance(got, list) and isinstance(expected, list):
            if len(got) != len(expected):
                return False
            for g, e in zip(got, expected):
                if e is None and isinstance(g, int):
                    continue
                if g is None and e is None:
                    continue
                if g is None and e == 'None':
                    continue
                if g != e:
                    return False
            return True

        if self._is_linked_list(expected):
            return self._compare_linked_lists(got, expected)

        if isinstance(expected, list) and isinstance(got, list):
            if len(expected) != len(got):
                return False
            if expected and not isinstance(expected[0], (list, dict)):
                return got == expected

            return all(self._compare_exact(g, e) for g, e in zip(got, expected))
        return False

    def _compare_sorted(self, got: Any, expected: Any) -> bool:
        """Compare sorted values (for order-independent results)."""
        try:
            if isinstance(got, list) and isinstance(expected, list):
                if len(got) != len(expected):
                    return False

                if got and isinstance(got[0], list):
                    got_sorted = [sorted(inner) for inner in got]
                    expected_sorted = [sorted(inner) for inner in expected]
                    got_sorted.sort()
                    expected_sorted.sort()
                    return got_sorted == expected_sorted

                return sorted(got) == sorted(expected)

            return got == expected
        except (TypeError, ValueError):
            return False

    def _compare_approx(self, got: Any, expected: Any) -> bool:
        """Compare floating point values with tolerance efficiently."""
        try:
            if isinstance(got, (int, float)) and isinstance(expected, (int, float)):
                return abs(got - expected) < 1e-6
            if isinstance(got, list) and isinstance(expected, list):
                if len(got) != len(expected):
                    return False

                if all(isinstance(g, (int, float)) and isinstance(e, (int, float)) for g, e in zip(got, expected)):
                    return all(abs(g - e) < 1e-6 for g, e in zip(got, expected))

                return all(self._compare_approx(g, e) for g, e in zip(got, expected))
            return got == expected
        except TypeError:
            return False

    def _is_linked_list(self, obj: Any) -> bool:
        """Check if object is a linked list node."""
        if obj is None:
            return True
        return hasattr(obj, "val") and hasattr(obj, "next")

    def _compare_linked_lists(self, got: Any, expected: Any) -> bool:
        """Compare two linked lists."""
        while expected is not None and got is not None:
            if getattr(expected, "val", None) != getattr(got, "val", None):
                return False
            expected = getattr(expected, "next", None)
            got = getattr(got, "next", None)
        return expected is None and got is None
