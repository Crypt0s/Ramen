# Copyright (C) 2008, Roger Demetrescu <roger.demetrescu@gmail.com>
# Copyright (C) 2008-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

from __future__ import unicode_literals

import unittest

import ftputil.error

from test import test_base
from test.test_file import InaccessibleDirSession, ReadMockSession
from test.test_host import FailOnLoginSession


# Exception raised by client code, i. e. code using ftputil. Used to
# test the behavior in case of client exceptions.
class ClientCodeException(Exception):
    pass


#
# Test cases
#
class TestHostContextManager(unittest.TestCase):

    def test_normal_operation(self):
        with test_base.ftp_host_factory() as host:
            self.assertEqual(host.closed, False)
        self.assertEqual(host.closed, True)

    def test_ftputil_exception(self):
        try:
            with test_base.ftp_host_factory(FailOnLoginSession) as host:
                pass
        except ftputil.error.FTPOSError:
            # We arrived here, that's fine. Because the `FTPHost` object
            # wasn't successfully constructed, the assignment to `host`
            # shouldn't have happened.
            self.assertFalse("host" in locals())
        else:
            raise self.failureException("ftputil.error.FTPOSError not raised")

    def test_client_code_exception(self):
        try:
            with test_base.ftp_host_factory() as host:
                self.assertEqual(host.closed, False)
                raise ClientCodeException()
        except ClientCodeException:
            self.assertEqual(host.closed, True)
        else:
            raise self.failureException("ClientCodeException not raised")


class TestFileContextManager(unittest.TestCase):

    def test_normal_operation(self):
        with test_base.ftp_host_factory(
               session_factory=ReadMockSession) as host:
            with host.open("dummy", "r") as f:
                self.assertEqual(f.closed, False)
                data = f.readline()
                self.assertEqual(data, "line 1\n")
                self.assertEqual(f.closed, False)
            self.assertEqual(f.closed, True)

    def test_ftputil_exception(self):
        with test_base.ftp_host_factory(
               session_factory=InaccessibleDirSession) as host:
            try:
                # This should fail since the directory isn't accessible
                # by definition.
                with host.open("/inaccessible/new_file", "w") as f:
                    pass
            except ftputil.error.FTPIOError:
                # The file construction shouldn't have succeeded, so
                # `f` should be absent from the local namespace.
                self.assertFalse("f" in locals())
            else:
                raise self.failureException(
                        "ftputil.error.FTPIOError not raised")

    def test_client_code_exception(self):
        with test_base.ftp_host_factory(
               session_factory=ReadMockSession) as host:
            try:
                with host.open("dummy", "r") as f:
                    self.assertEqual(f.closed, False)
                    raise ClientCodeException()
            except ClientCodeException:
                self.assertEqual(f.closed, True)
            else:
                raise self.failureException("ClientCodeException not raised")


if __name__ == "__main__":
    unittest.main()
