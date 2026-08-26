"""
Auto-tester for author solutions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from problem_repository import ProblemRepository
from code_runner import CodeRunner


def test_all_author_solutions():
    """Test all author solutions against their problems."""

    base_dir = Path(__file__).parent
    problems_dir = base_dir / "data" / "problems"
    db_path = base_dir / "data" / "problems_db.json"

    print("=" * 70)
    print("ALGO TRAINER - AUTHOR SOLUTIONS AUTO-TESTER")
    print("=" * 70)

    print("\n[1/3] Initializing ProblemRepository...")
    repo = ProblemRepository(str(problems_dir), str(db_path))
    repo.initialize()

    print(f"      Loaded {len(repo._problems)} problems")

    print("\n[2/3] Initializing CodeRunner...")
    runner = CodeRunner()

    print("\n[3/3] Testing author solutions...\n")

    results = {
        "passed": [],
        "failed": [],
        "no_solution": [],
        "errors": []
    }

    for problem_id in sorted(repo._problems.keys()):
        problem = repo.get_by_id(problem_id)

        if not problem:
            results["errors"].append({
                "id": problem_id,
                "title": "Unknown",
                "error": "Problem not found"
            })
            continue

        title = problem.get("title", "Unknown")
        author_solution = problem.get("author_solution")

        if not author_solution or not author_solution.strip():
            results["no_solution"].append({
                "id": problem_id,
                "title": title
            })
            continue

        template = problem.get("template", "")
        func_name = problem.get("function", "")

        auto_imports = """from typing import List, Optional, Tuple, Dict, Set, Any
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
"""

        if author_solution.strip().startswith(f"def {func_name}("):
            full_code = auto_imports + '\n' + author_solution
        elif f"class {func_name}:" in author_solution or author_solution.strip().startswith("class "):
            full_code = auto_imports + '\n' + author_solution
        else:
            template_stripped = template.rstrip()

            author_lines = author_solution.split('\n')

            min_indent = 999
            for line in author_lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)

            if min_indent == 999:
                min_indent = 0

            processed_lines = []
            for line in author_lines:
                if line.strip():
                    stripped = line[min_indent:] if len(line) > min_indent else line
                    processed_lines.append('    ' + stripped)
                else:
                    processed_lines.append('')

            template_for_body = template.rstrip()
            full_code = template_for_body + '\n' + '\n'.join(processed_lines)

        test_results = runner.run_tests(full_code, problem)

        summary = test_results.get("summary", "")
        passed_all = summary.startswith(str(len(problem.get('tests', [])))) and '✅' in summary

        if passed_all:
            results["passed"].append({
                "id": problem_id,
                "title": title,
                "summary": summary
            })
        else:
            failed_test = None
            for r in test_results.get("results", []):
                if not r.get("passed"):
                    failed_test = r
                    break

            results["failed"].append({
                "id": problem_id,
                "title": title,
                "summary": test_results.get("summary", "Unknown error"),
                "error": test_results.get("error"),
                "failed_test": failed_test
            })

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if results["passed"]:
        print(f"\n✅ PASSED ({len(results['passed'])}):")
        for r in results["passed"]:
            print(f"   ✓ ID {r['id']}: {r['title']} - {r['summary']}")

    if results["failed"]:
        print(f"\n❌ FAILED ({len(results['failed'])}):")
        for r in results["failed"]:
            print(f"\n   ✗ ID {r['id']}: {r['title']}")
            print(f"      Summary: {r['summary']}")
            if r.get('error'):
                print(f"      Error: {r['error']}")
            if r.get('failed_test'):
                ft = r['failed_test']
                print(f"      Test {ft.get('test_num', '?')}: {ft.get('error', 'Failed')}")
                if ft.get('args'):
                    print(f"      Input: {ft['args']}")
                if ft.get('expected'):
                    print(f"      Expected: {ft['expected']}")
                if ft.get('got'):
                    print(f"      Got: {ft['got']}")

    if results["no_solution"]:
        print(f"\n⚠️  NO AUTHOR SOLUTION ({len(results['no_solution'])}):")
        for r in results["no_solution"]:
            print(f"   ○ ID {r['id']}: {r['title']}")

    if results["errors"]:
        print(f"\n💥 ERRORS ({len(results['errors'])}):")
        for r in results["errors"]:
            print(f"   ✗ ID {r['id']}: {r['error']}")

    print("\n" + "=" * 70)
    total_with_solution = len(results["passed"]) + len(results["failed"])
    total = total_with_solution + len(results["no_solution"])
    pass_rate = (len(results["passed"]) / total_with_solution * 100) if total_with_solution > 0 else 0

    print(f"SUMMARY: {len(results['passed'])}/{total_with_solution} passed ({pass_rate:.1f}%)")
    print(f"         {len(results['failed'])} failed")
    print(f"         {len(results['no_solution'])} without author solution")
    print(f"         {total} total problems")
    print("=" * 70)

    if results["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = test_all_author_solutions()
    sys.exit(exit_code)
