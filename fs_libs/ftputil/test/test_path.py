# encoding: utf-8
# Copyright (C) 2003-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

from __future__ import unicode_literals

import ftplib
import time
import unittest

import ftputil
import ftputil.compat
import ftputil.error
import ftputil.tool

from test import mock_ftplib
from test import test_base


class FailingFTPHost(ftputil.FTPHost):

    def _dir(self, path):
        raise ftputil.error.FTPOSError("simulate a failure, e. g. timeout")


# Mock session, used for testing an inaccessible login directory
class SessionWithInaccessibleLoginDirectory(mock_ftplib.MockSession):

    def cwd(self, dir):
        # Assume that `dir` is the inaccessible login directory.
        raise ftplib.error_perm("can't change into this directory")


class TestPath(unittest.TestCase):
    """Test operations in `FTPHost.path`."""

    def test_regular_isdir_isfile_islink(self):
        """Test regular `FTPHost._Path.isdir/isfile/islink`."""
        host = test_base.ftp_host_factory()
        testdir = "/home/sschwarzer"
        host.chdir(testdir)
        # Test a path which isn't there.
        self.assertFalse(host.path.isdir ("notthere"))
        self.assertFalse(host.path.isfile("notthere"))
        self.assertFalse(host.path.islink("notthere"))
        #  This checks additional code (see ticket #66).
        self.assertFalse(host.path.isdir ("/notthere/notthere"))
        self.assertFalse(host.path.isfile("/notthere/notthere"))
        self.assertFalse(host.path.islink("/notthere/notthere"))
        # Test a directory.
        self.assertTrue (host.path.isdir (testdir))
        self.assertFalse(host.path.isfile(testdir))
        self.assertFalse(host.path.islink(testdir))
        # Test a file.
        testfile = "/home/sschwarzer/index.html"
        self.assertFalse(host.path.isdir (testfile))
        self.assertTrue (host.path.isfile(testfile))
        self.assertFalse(host.path.islink(testfile))
        # Test a link. Since the link target of `osup` doesn't exist,
        # neither `isdir` nor `isfile` return `True`.
        testlink = "/home/sschwarzer/osup"
        self.assertFalse(host.path.isdir (testlink))
        self.assertFalse(host.path.isfile(testlink))
        self.assertTrue (host.path.islink(testlink))

    def test_workaround_for_spaces(self):
        """Test whether the workaround for space-containing paths is used."""
        host = test_base.ftp_host_factory()
        testdir = "/home/sschwarzer"
        host.chdir(testdir)
        # Test a file name containing spaces.
        testfile = "/home/dir with spaces/file with spaces"
        self.assertFalse(host.path.isdir (testfile))
        self.assertTrue (host.path.isfile(testfile))
        self.assertFalse(host.path.islink(testfile))

    def test_inaccessible_home_directory_and_whitespace_workaround(self):
        "Test combination of inaccessible home directory + whitespace in path."
        host = test_base.ftp_host_factory(
               session_factory=SessionWithInaccessibleLoginDirectory)
        self.assertRaises(ftputil.error.InaccessibleLoginDirError,
                          host._dir, "/home dir")

    def test_isdir_isfile_islink_with_exception(self):
        """Test failing `FTPHost._Path.isdir/isfile/islink`."""
        host = test_base.ftp_host_factory(ftp_host_class=FailingFTPHost)
        testdir = "/home/sschwarzer"
        host.chdir(testdir)
        # Test if exceptions are propagated.
        FTPOSError = ftputil.error.FTPOSError
        self.assertRaises(FTPOSError, host.path.isdir,  "index.html")
        self.assertRaises(FTPOSError, host.path.isfile, "index.html")
        self.assertRaises(FTPOSError, host.path.islink, "index.html")

    def test_exists(self):
        """Test `FTPHost.path.exists`."""
        # Regular use of `exists`
        host = test_base.ftp_host_factory()
        testdir = "/home/sschwarzer"
        host.chdir(testdir)
        self.assertTrue (host.path.exists("index.html"))
        self.assertFalse(host.path.exists("notthere"))
        # Test if exceptions are propagated.
        host = test_base.ftp_host_factory(ftp_host_class=FailingFTPHost)
        self.assertRaises(
          ftputil.error.FTPOSError, host.path.exists, "index.html")


class TestAcceptEitherBytesOrUnicode(unittest.TestCase):

    def setUp(self):
        self.host = test_base.ftp_host_factory()

    def _test_method_string_types(self, method, path):
        expected_type = type(path)
        self.assertTrue(isinstance(method(path), expected_type))

    def test_methods_that_take_and_return_one_string(self):
        """
        Test whether the same string type as for the argument is returned.
        """
        bytes_type = ftputil.compat.bytes_type
        unicode_type = ftputil.compat.unicode_type
        method_names = ("abspath basename dirname join normcase normpath".
                        split())
        for method_name in method_names:
            method = getattr(self.host.path, method_name)
            self._test_method_string_types(method,  "/")
            self._test_method_string_types(method,  ".")
            self._test_method_string_types(method, b"/")
            self._test_method_string_types(method, b".")

    def test_methods_that_take_a_string_and_return_a_bool(self):
        """Test whether the methods accept byte and unicode strings."""
        host = self.host
        as_bytes = ftputil.tool.as_bytes
        host.chdir("/home/file_name_test")
        # `isabs`
        self.assertFalse(host.path.isabs("ä"))
        self.assertFalse(host.path.isabs(as_bytes("ä")))
        # `exists`
        self.assertTrue(host.path.exists("ä"))
        self.assertTrue(host.path.exists(as_bytes("ä")))
        # `isdir`, `isfile`, `islink`
        self.assertTrue(host.path.isdir ("ä"))
        self.assertTrue(host.path.isdir (as_bytes("ä")))
        self.assertTrue(host.path.isfile("ö"))
        self.assertTrue(host.path.isfile(as_bytes("ö")))
        self.assertTrue(host.path.islink("ü"))
        self.assertTrue(host.path.islink(as_bytes("ü")))

    def test_join(self):
        """
        Test whether `FTPHost.path.join` accepts only arguments of
        the same string type and returns the same string type.
        """
        join = self.host.path.join
        as_bytes = ftputil.tool.as_bytes
        # Only unicode
        parts = list("äöü")
        result = join(*parts)
        self.assertEqual(result, "ä/ö/ü")
        #  Need explicit type check for Python 2
        self.assertTrue(isinstance(result, ftputil.compat.unicode_type))
        # Only bytes
        parts = [as_bytes(s) for s in "äöü"]
        result = join(*parts)
        self.assertEqual(result, as_bytes("ä/ö/ü"))
        #  Need explicit type check for Python 2
        self.assertTrue(isinstance(result, ftputil.compat.bytes_type))
        # Mixture of unicode and bytes
        parts = ["ä", as_bytes("ö")]
        self.assertRaises(TypeError, join, *parts)
        parts = [as_bytes("ä"), as_bytes("ö"), "ü"]
        self.assertRaises(TypeError, join, *parts)

    def test_getmtime(self):
        """
        Test whether `FTPHost.path.getmtime` accepts byte and unicode
        paths.
        """
        host = self.host
        as_bytes = ftputil.tool.as_bytes
        host.chdir("/home/file_name_test")
        # We don't care about the _exact_ time, so don't bother with
        # timezone differences. Instead, do a simple sanity check.
        day = 24 * 60 * 60  # seconds
        expected_mtime = time.mktime((2000, 5, 29, 0, 0, 0, 0, 0, 0))
        mtime_makes_sense = (lambda mtime: expected_mtime - day <= mtime <=
                                           expected_mtime + day)
        self.assertTrue(mtime_makes_sense(host.path.getmtime("ä")))
        self.assertTrue(mtime_makes_sense(host.path.getmtime(as_bytes("ä"))))

    def test_getsize(self):
        """
        Test whether `FTPHost.path.getsize` accepts byte and unicode paths.
        """
        host = self.host
        as_bytes = ftputil.tool.as_bytes
        host.chdir("/home/file_name_test")
        self.assertEqual(host.path.getsize("ä"), 512)
        self.assertEqual(host.path.getsize(as_bytes("ä")), 512)

    def test_walk(self):
        """Test whether `FTPHost.path.walk` accepts bytes and unicode paths."""
        host = self.host
        as_bytes = ftputil.tool.as_bytes
        def noop(arg, top, names):
            del names[:]
        host.path.walk("ä", noop, None)
        host.path.walk(as_bytes("ä"), noop, None)


if __name__ == "__main__":
    unittest.main()
