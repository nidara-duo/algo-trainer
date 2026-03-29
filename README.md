# Algo Trainer

Desktop application for practicing Python coding problems (similar to LeetCode).

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## Features

- **31 coding problems** with 1155+ test cases
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
git clone https://github.com/YOUR_USERNAME/algo-trainer.git
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
│   ├── raw_problems/       # 31 problem files
│   ├── solutions/          # Author solutions
│   └── problems_db.json    # Cached problems
│
├── test_generator/
│   ├── base.py             # TestGenerator base class
│   ├── runner.py           # Generation orchestrator
│   └── generators/         # 31 problem generators
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

Expected output: **31/31 passed (100.0%)**

## Problem List

| ID | Problem | Difficulty | Tests |
|----|---------|------------|-------|
| 1 | Two Sum | Easy | 53 |
| 2 | Add Two Numbers | Medium | 36 |
| 3 | Longest Substring Without Repeating Characters | Medium | 38 |
| 6 | ZigZag Conversion | Medium | 37 |
| 49 | Group Anagrams | Medium | 41 |
| 56 | Merge Intervals | Medium | 42 |
| 88 | Merge Sorted Array | Easy | 30 |
| 104 | Maximum Depth of Binary Tree | Easy | 37 |
| 125 | Valid Palindrome | Easy | 37 |
| 161 | One Edit Distance | Medium | 40 |
| 206 | Reverse Linked List | Easy | 36 |
| 228 | Summary Ranges | Easy | 37 |
| 238 | Product of Array Except Self | Medium | 36 |
| 283 | Move Zeroes | Easy | 36 |
| 356 | Line Reflection | Medium | 37 |
| 380 | Insert Delete GetRandom O(1) | Medium | 30 |
| 392 | Is Subsequence | Easy | 37 |
| 443 | String Compression | Easy | 37 |
| 652 | Find Duplicate Subtrees | Medium | 36 |
| 658 | Find K Closest Elements | Medium | 36 |
| 680 | Valid Palindrome II | Easy | 37 |
| 1004 | Max Consecutive Ones III | Medium | 36 |
| 1438 | Longest Subarray with Absolute Diff | Medium | 37 |
| 1493 | Longest Subarray of 1's | Easy | 37 |
| 10000 | Reconstruct Journey Path (Yandex) | Medium | 37 |
| 10001 | Remove Consecutive Spaces (Yandex) | Easy | 36 |
| 10002 | Compress Ranges (Yandex) | Easy | 39 |
| 10003 | Find Equivalent Subtrees (Yandex) | Medium | 35 |
| 10005 | One Edit Distance (Yandex) | Medium | 40 |
| 10006 | Search in Bitonic Array (Yandex) | Medium | 37 |
| 10007 | Common Prefix of Two Permutations (Yandex) | Medium | 35 |

## Architecture

### Backend (Python)

- **ProblemRepository** - Loads and caches coding problems from .txt files
- **CodeRunner** - Executes user code with timeout protection (0.5s per test, 3s total)
- **StatisticsManager** - Tracks user progress and submissions

### Frontend (JavaScript)

- **Monaco Editor** - Python syntax highlighting, auto-indentation
- **localStorage** - Code persistence per problem
- **Dark theme** - Port from C++/FLTK implementation

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
- **Original C++/FLTK implementation** - Reference design
