
"""
Generate Tests for Algo Trainer Problems

This script generates test cases for coding problems using their author solutions.

Usage:
    python generate_tests.py --problem-id 1 --count 20
    python generate_tests.py --all --count 10
    python generate_tests.py -p 49 -c 15
"""

import sys
from test_generator.runner import main

if __name__ == '__main__':
    main()
