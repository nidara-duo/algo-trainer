# Algo Trainer

Desktop application for practicing Python coding problems (similar to LeetCode).

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## Features

- **32 coding problems** with 1185+ test cases
- **Monaco Editor** - the same editor that powers VS Code
- **Automated test generation** from author solutions
- **100% test coverage** - all author solutions verified
- **Dark theme** optimized for long coding sessions
- **Progress tracking** with detailed statistics
- **10-minute timer** per problem
- **Resizable panels** for optimal layout

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/nidara-duo/algo-trainer.git
cd algo-trainer

# Install dependencies
pip install pywebview
```

### Running

```bash
python main.py
```

The application will launch in a native window (1400x700, resizable).

## Project Structure

```
algo-trainer/
├── main.py                 # Entry point
├── api.py                  # pywebview API bridge
├── problem_repository.py   # Problem loader
├── code_runner.py          # Test executor
├── statistics.py           # Statistics manager
├── generate_tests.py       # Test generation CLI
├── test_author_solutions.py # Verification script
│
├── ui/
│   ├── main.js             # Frontend logic
│   ├── style.css           # Monaco dark theme
│   └── editor_config.js    # Monaco configuration
│
├── vs/                     # Monaco Editor (minimized)
│
├── data/
│   ├── raw_problems/       # 7 problem files
│   ├── solutions/          # Author solutions
│   └── problems_db.json    # Cached problems
│
├── test_generator/
│   ├── base.py             # TestGenerator base class
│   ├── runner.py           # Generation orchestrator
│   └── generators/         # 7 problem generators
│
└── docs/
    └── OPTIMIZATIONS.md    # Performance guide
```

## Test Generation

Generate additional test cases from author solutions:

```bash
# Generate 20 tests for all problems
python generate_tests.py --all --count 20

# Generate tests for specific problem
python generate_tests.py --problem-id 1 --count 20

# Replace existing tests
python generate_tests.py -p 49 -c 15 --replace
```

## Verification

Run the test suite to verify all author solutions:

```bash
python test_author_solutions.py
```

Expected output: **32/32 passed (100.0%)**

## Problem List

| ID | Problem | Difficulty | Tests |
|----|---------|------------|-------|
| 1 | Two Sum | Easy | 53 |
| 2 | Add Two Numbers | Medium | 36 |
| 3 | Longest Substring Without Repeating Characters | Medium | 38 |
| 6 | ZigZag Conversion | Medium | 37 |
| 20 | Valid Parentheses | Easy | 30 |
| 49 | Group Anagrams | Medium | 41 |
| 56 | Merge Intervals | Medium | 42 |


## Architecture

### Backend (Python)

- **ProblemRepository** - Loads and caches coding problems from .txt files
- **CodeRunner** - Executes user code with timeout protection (0.5s per test, 3s total)
- **StatisticsManager** - Tracks user progress and submissions

### Frontend (JavaScript)

- **Monaco Editor** - Python syntax highlighting, auto-indentation
- **localStorage** - Code persistence per problem

### Performance Optimizations

| Optimization | Impact |
|--------------|--------|
| Monaco minimization | 70% smaller bundle |
| ProcessPoolExecutor | ~100ms savings per test |
| Cached imports | 30% faster execution |
| os.scandir() | 3-5x faster file I/O |

## Development

### Adding a New Problem

1. Create `data/raw_problems/{id}_{slug}.txt` with problem metadata
2. Create `data/solutions/{id}.txt` with author solution
3. Delete `data/problems_db.json` (will regenerate on next launch)
4. Restart the application

### Adding a New Test Generator

1. Create `test_generator/generators/{problem_name}.py`
2. Inherit from `TestGenerator` base class
3. Implement `generate()` method
4. Register in `test_generator/runner.py`

## Requirements

- Python 3.8+
- pywebview

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **Monaco Editor** - https://github.com/microsoft/monaco-editor
