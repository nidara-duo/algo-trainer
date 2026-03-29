"""
Problem Repository - loads and caches coding problems from .txt files.

This module provides automatic template generation from metadata fields.
Template signatures are generated from FUNCTION, ARGUMENTS, and RETURN_TYPE fields.
"""

import json
import os
import re
import ast
import tempfile
from pathlib import Path
from typing import Optional


class ProblemRepository:
    """Manages loading, caching, and synchronization of coding problems."""

    def __init__(self, source_dir: str, db_path: str):
        self.__source_dir = Path(source_dir)
        self.__db_path = Path(db_path)
        self.__solutions_dir = self.__source_dir.parent / "solutions"
        self._problems: dict[int, dict] = {}
        self._file_mtimes: dict[str, float] = {}

    def initialize(self) -> None:
        """Load problems from database or build from .txt files."""
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

    def _parse_txt(self, path: Path) -> dict:
        """Parse a .txt problem file into a dictionary."""
        content = path.read_text(encoding="utf-8")

        problem = {
            "id": None,
            "title": "",
            "difficulty": "",
            "matchmode": "exact",
            "function": "",
            "arguments": [],
            "return_type": "",
            "condition": "",
            "template": "",
            "tests": [],
        }

        sections = self._split_into_sections(content)

        problem["id"] = int(self._extract_field(sections.get("header", ""), "ID"))
        problem["title"] = self._extract_field(sections.get("header", ""), "TITLE")
        problem["difficulty"] = self._extract_field(sections.get("header", ""), "DIFFICULTY")
        problem["matchmode"] = self._extract_field(sections.get("header", ""), "MATCHMODE") or "exact"
        problem["function"] = self._extract_field(sections.get("header", ""), "FUNCTION")

        args_str = self._extract_field(sections.get("header", ""), "ARGUMENTS")
        if args_str:
            problem["arguments"] = json.loads(args_str)

        problem["return_type"] = self._extract_field(sections.get("header", ""), "RETURN_TYPE")

        examples_count_str = self._extract_field(sections.get("header", ""), "EXAMPLES")
        try:
            examples_count = int(examples_count_str) if examples_count_str else 2
        except ValueError:
            examples_count = 2

        base_condition = sections.get("condition", "")

        problem["template"] = self._generate_template({
            "function": problem["function"],
            "arguments": problem["arguments"],
            "return_type": problem["return_type"],
        })

        tests = []
        tests_section = sections.get("tests", "")
        if tests_section:
            for line in tests_section.split("\n"):
                line_stripped = line.strip()
                if line_stripped:
                    test_data = self._parse_test_line(line_stripped)
                    if test_data:
                        tests.append(test_data)

        problem["tests"] = tests

        problem["condition"] = self._generate_condition_with_examples(
            base_condition,
            problem["arguments"],
            tests,
            examples_count
        )

        problem["author_solution"] = self._load_author_solution(problem["id"])

        return problem

    def _parse_test_line(self, line: str) -> Optional[dict]:
        """Parse a test line in the new format."""
        import re

        pattern = r'<args>(.*?)</args>;\s*<output>(.*?)</output>'
        match = re.match(pattern, line.strip(), re.DOTALL)

        if not match:
            print(f"Warning: Could not parse test line: {line}")
            return None

        args_str = match.group(1).strip()
        output_str = match.group(2).strip()

        args = self._parse_args_string(args_str)

        output_str = output_str.replace('null', 'None')
        output_str = output_str.replace('false', 'False').replace('true', 'True')
        try:
            expected = ast.literal_eval(output_str)
        except (ValueError, SyntaxError) as e:
            print(f"Warning: Could not parse output '{output_str}': {e}")
            expected = output_str

        return {
            "args": args,
            "expected": expected,
        }

    def _parse_args_string(self, args_str: str) -> list:
        """Parse args string and return a list of parsed arguments."""
        import re

        args_str = args_str.strip()

        depth = 0
        in_string = False
        string_char = None
        has_comma_at_depth_0 = False

        for char in args_str:
            if char in ('"', "'"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            elif char in ('[', '{', '(') and not in_string:
                depth += 1
            elif char in (']', '}', ')') and not in_string:
                depth -= 1
            elif char == ',' and depth == 0 and not in_string:
                has_comma_at_depth_0 = True
                break

        if not has_comma_at_depth_0:
            if (args_str.startswith('[') and args_str.endswith(']')) or \
               (args_str.startswith('{') and args_str.endswith('}')):
                try:
                    return [ast.literal_eval(args_str)]
                except (ValueError, SyntaxError):
                    pass

        args = []
        current_arg = ""
        depth = 0
        in_string = False
        string_char = None

        for char in args_str:
            if char in ('"', "'"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                current_arg += char
            elif char in ('[', '{', '(') and not in_string:
                depth += 1
                current_arg += char
            elif char in (']', '}', ')') and not in_string:
                depth -= 1
                current_arg += char
            elif char == ',' and depth == 0 and not in_string:
                arg_stripped = current_arg.strip()
                if arg_stripped:
                    try:
                        args.append(ast.literal_eval(arg_stripped))
                    except (ValueError, SyntaxError):
                        args.append(arg_stripped)
                current_arg = ""
            else:
                current_arg += char

        arg_stripped = current_arg.strip()
        if arg_stripped:
            try:
                args.append(ast.literal_eval(arg_stripped))
            except (ValueError, SyntaxError):
                args.append(arg_stripped)

        return args

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

    def _split_into_sections(self, content: str) -> dict[str, str]:
        """Split file content into named sections using regex."""
        pattern = r'^((?:CONDITION|TEMPLATE|IMPORTS|TESTS):)'
        parts = re.split(pattern, content, flags=re.MULTILINE)

        sections = {"header": parts[0] if parts else ""}

        for i in range(1, len(parts), 2):
            marker = parts[i].strip(':').lower()
            content_part = parts[i + 1] if i + 1 < len(parts) else ""
            sections[marker] = content_part

        for key in ["condition", "template", "tests"]:
            if key not in sections:
                sections[key] = ""

        return sections

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

    def _extract_field(self, header_text: str, field_name: str) -> str:
        """Extract a field value from the header section."""
        pattern = rf"^{field_name}:\s*(.*)$"
        match = re.search(pattern, header_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""

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

        import os
        current_mtimes = {}
        try:
            with os.scandir(self.__source_dir) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.endswith('.txt'):
                        current_mtimes[entry.name] = entry.stat().st_mtime
        except (OSError, IOError):
            return True

        if stored_mtimes != current_mtimes:
            self._file_mtimes = current_mtimes
            return True

        self._file_mtimes = current_mtimes
        return False

    def _sync_database(self) -> None:
        """Synchronize database with current .txt files."""
        import os
        from pathlib import Path

        try:
            with os.scandir(self.__source_dir) as entries:
                txt_files = sorted(
                    (entry for entry in entries if entry.is_file() and entry.name.endswith('.txt')),
                    key=lambda e: e.name
                )
        except (OSError, IOError):
            return

        for txt_file in txt_files:
            try:
                problem = self._parse_txt(Path(txt_file.path))
                self._problems[problem["id"]] = problem
                self._file_mtimes[txt_file.name] = txt_file.stat().st_mtime
            except Exception as e:
                print(f"Error parsing {txt_file.path}: {e}")

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
