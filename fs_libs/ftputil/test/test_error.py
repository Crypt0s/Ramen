# encoding: utf-8
# Copyright (C) 2002-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

from __future__ import unicode_literals

import ftplib
import unittest

import ftputil.error


class TestFTPErrorArguments(unittest.TestCase):
    """
    The `*Error` constructors should accept either a byte string or a
    unicode string.
    """

    def test_bytestring_argument(self):
        # An umlaut as latin-1 character
        io_error = ftputil.error.FTPIOError(b"\xe4")
        os_error = ftputil.error.FTPOSError(b"\xe4")

    def test_unicode_argument(self):
        # An umlaut as unicode character
        io_error = ftputil.error.FTPIOError("\xe4")
        os_error = ftputil.error.FTPOSError("\xe4")


class TestErrorConversion(unittest.TestCase):

    def callee(self):
        raise ftplib.error_perm()

    def test_ftplib_error_to_ftp_os_error(self):
        """
        Ensure the `ftplib` exception isn't used as `FTPOSError`
        argument.
        """
        try:
            with ftputil.error.ftplib_error_to_ftp_os_error:
                self.callee()
        except ftputil.error.FTPOSError as exc:
            self.assertFalse(exc.args and
                             isinstance(exc.args[0], ftplib.error_perm))
        else:
            # We shouldn't come here.
            self.assertTrue(False)

    def test_ftplib_error_to_ftp_io_error(self):
        """
        Ensure the `ftplib` exception isn't used as `FTPIOError`
        argument.
        """
        try:
            with ftputil.error.ftplib_error_to_ftp_io_error:
                self.callee()
        except ftputil.error.FTPIOError as exc:
            self.assertFalse(exc.args and
                             isinstance(exc.args[0], ftplib.error_perm))
        else:
            # We shouldn't come here.
            self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
