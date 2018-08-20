#!/usr/bin/env python

# Building out test suite based on example:
# https://github.com/django/django/tree/master/tests

import argparse
import os

import tinman
from tinman.test import TestCase, TransactionTestCase
from tinman.test.runner import default_test_processes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Tinman test suite.")
    parser.add_argument(
        '-v', '--verbosity', default=1, type=int, choices=[0, 1, 2, 3],
        help='Verbosity level; 0=minimal output, 1=normal output, 2=all output',
    )
    parser.add_argument(
        '--failfast', action='store_true',
        help='Tells Tinman to stop running the test suite after first failed test.',
    )
    parser.add_argument(
        '--parallel', nargs='?', default=0, type=int,
        const=default_test_processes(), metavar='N',
        help='Run tests using up to N parallel processes.',
    )

    options = parser.parse_args()

    # Allow including a trailing slash on app_labels for tab completion convenience
    options.modules = [os.path.normpath(labels) for labels in options.modules]

    failures = tinman_tests(
        options.verbosity, options.failfast, options.parallel
    )
    if failures:
        sys.exit(1)
