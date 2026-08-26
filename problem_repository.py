"""
Problem Repository - loads and caches coding problems from .yaml files.

This module provides automatic template generation from metadata fields.
Template signatures are generated from FUNCTION, ARGUMENTS, and RETURN_TYPE fields.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import yaml


class ProblemRepository:
    """Manages loading, caching, and synchronization of coding problems."""

    def __init__(self, problems_dir: str, db_path: str):
        self.__problems_dir = Path(problems_dir)
        self.__db_path = Path(db_path)
        self.__solutions_dir = self.__problems_dir.parent / "solutions"
        self._problems: dict[int, dict] = {}
        self._file_mtimes: dict[str, float] = {}

    def initialize(self) -> None:
        """Load problems from database or build from .yaml files."""
        if self.__db_path.exists() and not self._needs_sync():
            self._load_database()
        else:
            self._sync_database()

    def get_problem_summaries(self) -> list[dict]:
        """Get list of problem summaries for UI display."""
        summaries = []
        for pid, problem in sorted(self._problems.items(), key=lambda x: int(x[0])):
            summaries.append({
                "id": problem["id"],
                "title": problem["title"],
                "difficulty": problem["difficulty"],
            })
        return summaries

    def get_by_id(self, problem_id: int) -> Optional[dict]:
        """Get full problem data by ID."""
        problem = self._problems.get(problem_id)
        if problem is None:
            return None

        if "author_solution" not in problem:
            problem["author_solution"] = self._load_author_solution(problem_id)

        return problem

    def _parse_yaml(self, path: Path) -> dict:
        """Parse a .yaml problem file into a dictionary."""
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        arguments = [
            {"name": arg["name"], "type": arg["type"]}
            for arg in (data.get("arguments") or [])
        ]

        tests = [
            {"args": list(test["args"]), "expected": test["output"]}
            for test in (data.get("tests") or [])
        ]

        examples_count = data.get("examples")
        if not isinstance(examples_count, int):
            examples_count = 2

        problem = {
            "id": int(data["id"]),
            "title": data.get("title", ""),
            "difficulty": data.get("difficulty", ""),
            "matchmode": data.get("matchmode") or "exact",
            "function": data.get("function", ""),
            "arguments": arguments,
            "return_type": data.get("return_type", ""),
            "condition": "",
            "template": "",
            "tests": tests,
        }

        problem["template"] = self._generate_template({
            "function": problem["function"],
            "arguments": problem["arguments"],
            "return_type": problem["return_type"],
        })

        problem["condition"] = self._generate_condition_with_examples(
            data.get("condition", "") or "",
            problem["arguments"],
            tests,
            examples_count
        )

        problem["author_solution"] = self._load_author_solution(problem["id"])

        return problem

    def _load_author_solution(self, problem_id: int) -> Optional[str]:
        """Load author solution from data/solutions/ directory."""
        if not self.__solutions_dir.exists():
            return None

        solution_file = self.__solutions_dir / f"{problem_id}.txt"
        if not solution_file.exists():
            return None

        try:
            return solution_file.read_text(encoding="utf-8")
        except Exception:
            return None

    def _generate_template(self, metadata: dict) -> str:
        """Generate Python function signature template from metadata."""
        func_name = metadata.get("function", "solution")
        arguments = metadata.get("arguments", [])
        return_type = metadata.get("return_type", "Any")

        args_parts = []
        for arg in arguments:
            arg_name = arg.get("name", "arg")
            arg_type = arg.get("type", "Any")
            args_parts.append(f"{arg_name}: {arg_type}")

        args_str = ", ".join(args_parts)

        template = f"def {func_name}({args_str}) -> {return_type}:\n    "

        return template

    def _generate_condition_with_examples(
        self,
        condition_html: str,
        arguments: list,
        tests: list,
        num_examples: int
    ) -> str:
        """Generate HTML examples section based on test cases."""
        if num_examples <= 0:
            return condition_html

        arg_names = [arg["name"] for arg in arguments]
        examples_html = "\n\n<h3>Examples</h3>"

        num_to_generate = min(num_examples, len(tests))

        for i in range(num_to_generate):
            test = tests[i]
            test_args = test["args"]
            expected = test["expected"]

            input_lines = []
            for name, value in zip(arg_names, test_args):
                input_lines.append(f"{name} = {repr(value)}")

            input_str = "\n".join(input_lines)
            output_str = repr(expected)

            examples_html += f"""
<p><strong>Example {i+1}:</strong></p>
<div class="example-block">
  <div class="example-section">
    <div class="example-label">Input:</div>
    <div class="example-content">{input_str}</div>
  </div>
  <div class="example-section">
    <div class="example-label">Output:</div>
    <div class="example-content"><code>{output_str}</code></div>
  </div>
</div>"""

        return condition_html + examples_html

    def _collect_source_files(self) -> list[Path]:
        """Collect .yaml problem source files."""
        try:
            with os.scandir(self.__problems_dir) as entries:
                files = [
                    Path(entry.path)
                    for entry in entries
                    if entry.is_file() and entry.name.endswith('.yaml')
                ]
        except (OSError, IOError):
            return []

        return sorted(files, key=lambda path: path.name)

    def _needs_sync(self) -> bool:
        """Check if database needs synchronization with source files."""
        if not self.__db_path.exists():
            return True

        try:
            with open(self.__db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
                stored_mtimes = db.get("_mtimes", {})
        except (json.JSONDecodeError, KeyError):
            return True

        current_mtimes: dict[str, float] = {}
        try:
            for source_file in self._collect_source_files():
                current_mtimes[source_file.name] = source_file.stat().st_mtime
        except (OSError, IOError):
            return True

        if stored_mtimes != current_mtimes:
            self._file_mtimes = current_mtimes
            return True

        self._file_mtimes = current_mtimes
        return False

    def _sync_database(self) -> None:
        """Synchronize database with current .yaml source files."""
        for source_file in self._collect_source_files():
            try:
                problem = self._parse_yaml(source_file)
                self._problems[problem["id"]] = problem
                self._file_mtimes[source_file.name] = source_file.stat().st_mtime
            except Exception as e:
                print(f"Error parsing {source_file}: {e}")

        self._save_database()

    def _save_database(self) -> None:
        """Save problems to database file atomically."""
        db_data = {
            "_mtimes": self._file_mtimes,
            "problems": self._problems,
        }

        self.__db_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=str(self.__db_path.parent),
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(db_data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, str(self.__db_path))
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _load_database(self) -> None:
        """Load problems from database file."""
        with open(self.__db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
            raw_problems = db.get("problems", {})
            self._problems = {int(k): v for k, v in raw_problems.items()}
            self._file_mtimes = db.get("_mtimes", {})
