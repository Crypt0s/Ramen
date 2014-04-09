"""
Setup for unit tests.
"""

import os
import unittest


__all__ = ["skip_long_running_test"]


def skip_long_running_test_condition():
    """
    Helper function to use with `unittest.skipIf`.

    This requires either Python >= 2.7 or the standalonge `unittest2`
    module.
    """
    skip_flag = os.environ.get("SKIP_LONG_RUNNING_TESTS", "0")
    return skip_flag == "1"


skip_long_running_test = unittest.skipIf(skip_long_running_test_condition(),
                                         "skipping long-running test")
