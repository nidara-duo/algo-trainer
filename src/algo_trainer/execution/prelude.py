"""Execution prelude: standard imports and LeetCode-style data structures."""

from __future__ import annotations

import heapq
import math
from collections import Counter, defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple  # noqa: UP035


class ListNode:
    """Singly-linked list node."""

    def __init__(self, val: int = 0, next: ListNode | None = None) -> None:
        self.val = val
        self.next = next


class TreeNode:
    """Binary tree node."""

    def __init__(
        self,
        val: int = 0,
        left: TreeNode | None = None,
        right: TreeNode | None = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right


def array_to_linked_list(arr: list[Any]) -> ListNode | None:
    """Convert a Python list to a linked list."""
    if not arr:
        return None
    head = ListNode(arr[0])
    current = head
    for val in arr[1:]:
        current.next = ListNode(val)
        current = current.next
    return head


def linked_list_to_array(head: ListNode | None) -> list[Any]:
    """Convert a linked list back to a Python list."""
    result: list[Any] = []
    current = head
    while current is not None:
        result.append(current.val)
        current = current.next
    return result


def array_to_tree(arr: list[Any]) -> TreeNode | None:
    """Convert a level-order list (with Nones) to a binary tree."""
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    queue: deque[TreeNode] = deque([root])
    i = 1
    while queue and i < len(arr):
        node = queue.popleft()
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root


def tree_to_array(root: TreeNode | None) -> list[Any]:
    """Convert a binary tree to a level-order list, trimming trailing Nones."""
    if root is None:
        return []
    result: list[Any] = []
    queue: deque[TreeNode | None] = deque([root])
    while queue:
        node = queue.popleft()
        if node is not None:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    while result and result[-1] is None:
        result.pop()
    return result


def build_namespace() -> dict[str, Any]:
    """Create a fresh isolated execution namespace with standard helpers."""
    return {
        "List": List,
        "Optional": Optional,
        "Tuple": Tuple,
        "Dict": Dict,
        "Set": Set,
        "Any": Any,
        "defaultdict": defaultdict,
        "Counter": Counter,
        "deque": deque,
        "heapq": heapq,
        "math": math,
        "ListNode": ListNode,
        "TreeNode": TreeNode,
        "array_to_linked_list": array_to_linked_list,
        "linked_list_to_array": linked_list_to_array,
        "array_to_tree": array_to_tree,
        "tree_to_array": tree_to_array,
    }
