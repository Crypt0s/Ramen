"""
Determine various types used in Python 2 and 3.

This program should be runnable in all Python versions, starting from
version 2.6.
"""

from __future__ import print_function
from __future__ import unicode_literals

import ftplib
import sys


class TypesTester(object):

    def __init__(self, callable):
        self.callable = callable

    def test_call(self, *args, **kwargs):
        should_print_result = kwargs.pop("print_result", False)
        print("Callable: {0}; Args: {1}; Kwargs: {2}".format(self.callable,
                                                             args, kwargs))
        try:
            result = self.callable(*args, **kwargs)
        except Exception as exc:
            print("Exception in `test_call`: {0}".format(exc))
        else:
            print("Result type: {0}".format(type(result)))
            if should_print_result:
                print("Result: {0!r}".format(result))
        print()
        return result


def test_types(callable, *args, **kwargs):
    tester = TypesTester(callable)
    return tester.test_call(*args, **kwargs)


def printer(*args, **kwargs):
    return TypesTester(print).test_call


def main():
    print("Running under Python {0.major}.{0.minor}.{0.micro} ...".
          format(sys.version_info))
    print()
    test_types(open, b"/etc/passwd", print_result=True)
    test_types(open, "/etc/passwd", print_result=True)
    ftp = ftplib.FTP("localhost", 'ftptest',
                     'd605581757de5eb56d568a4419f4126e')
    try:
        cwd = test_types(ftp.pwd, print_result=True)
        test_types(ftp.cwd, cwd)
        #ftp.retrlines("LIST", callback=printer())
    finally:
        ftp.close()


if __name__ == "__main__":
    main()
