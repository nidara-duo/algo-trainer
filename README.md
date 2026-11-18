# Algo Trainer

Desktop application for practicing Python coding problems (similar to LeetCode), powered by `pywebview` and Monaco Editor.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Python 3.12+ (managed automatically by `uv`)

## Quick Start

```bash
# Install dependencies and create virtual environment
uv sync

# Launch the desktop application
uv run algo-trainer
```

## Development Commands

```bash
# Run test suite
uv run pytest

# Validate all bundled YAML problems
uv run algo-trainer-check

# Lint & format
uv run ruff check .
uv run ruff format .

# Type-check core packages
uv run mypy
```

## Project Structure

```text
algo-trainer/
├── pyproject.toml                 # uv / hatchling config, dependencies, tooling
├── uv.lock                        # Locked dependency graph
├── .python-version                # Pinned Python 3.12
├── src/algo_trainer/
│   ├── app.py                     # Composition root & pywebview window launch
│   ├── cli.py                     # YAML problem validator (`algo-trainer-check`)
│   ├── config.py                  # Paths & execution limits
│   ├── domain/                    # Value objects, enums, errors, matchers
│   ├── problems/                  # YAML problem loader & repository
│   ├── rendering/                 # Code template & HTML example rendering
│   ├── execution/                 # Isolated worker pool, harness & prelude
│   ├── stats/                     # Submission store & statistics service
│   ├── infra/                     # Atomic JSON I/O
│   └── bridge/                    # pywebview JS-to-Python RPC facade
├── tests/                         # pytest unit & integration tests
├── data/problems/                 # Coding problems in YAML format
├── ui/                            # Frontend JS/CSS
├── vs/                            # Monaco Editor bundle
└── index.html                     # Main HTML entry
```

## Adding a New Problem

Create a `.yaml` file in `data/problems/` with `id`, `title`, `difficulty`, `function`, `arguments`, `return_type`, `condition`, and `tests` (optionally `matchmode`, `invocation: function|class`, `examples`, `solution`).

Verify the problem file with:

```bash
uv run algo-trainer-check
```
