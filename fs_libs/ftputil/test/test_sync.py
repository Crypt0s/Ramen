# Copyright (C) 2007-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

from __future__ import absolute_import
from __future__ import unicode_literals

import io
import ntpath
import os
import shutil
import unittest

import ftputil
import ftputil.sync


# Assume the test subdirectories are or will be in the current directory.
TEST_ROOT = os.getcwd()


class TestLocalToLocal(unittest.TestCase):

    def setUp(self):
        if not os.path.exists("test_empty"):
            os.mkdir("test_empty")
        if os.path.exists("test_target"):
            shutil.rmtree("test_target")
        os.mkdir("test_target")

    def test_sync_empty_dir(self):
        source = ftputil.sync.LocalHost()
        target = ftputil.sync.LocalHost()
        syncer = ftputil.sync.Syncer(source, target)
        source_dir = os.path.join(TEST_ROOT, "test_empty")
        target_dir = os.path.join(TEST_ROOT, "test_target")
        syncer.sync(source_dir, target_dir)

    def test_source_with_and_target_without_slash(self):
        source = ftputil.sync.LocalHost()
        target = ftputil.sync.LocalHost()
        syncer = ftputil.sync.Syncer(source, target)
        source_dir = os.path.join(TEST_ROOT, "test_source/")
        target_dir = os.path.join(TEST_ROOT, "test_target")
        syncer.sync(source_dir, target_dir)


# Helper classes for `TestUploadFromWindows`

class LocalWindowsHost(ftputil.sync.LocalHost):

    def __init__(self):
        self.path = ntpath
        self.sep = "\\"

    def open(self, path, mode):
        # Just return a dummy file object.
        return io.StringIO("")

    def walk(self, root):
        """
        Return a list of tuples as `os.walk`, but use tuples as if the
        directory structure was

        <root>
            dir1
                dir11
                file1
                file2

        where <root> is the string passed in as `root`.
        """
        join = ntpath.join
        return [(root,
                 [join(root, "dir1")],
                 []),
                (join(root, "dir1"),
                 ["dir11"],
                 ["file1", "file2"])
                ]


class DummyFTPSession(object):

    def pwd(self):
        return "/"


class DummyFTPPath(object):

    def abspath(self, path):
        # Don't care here if the path is absolute or not.
        return path

    def isdir(self, path):
        return ("dir" in path)

    def isfile(self, path):
        return ("file" in path)


class ArgumentCheckingFTPHost(ftputil.FTPHost):

    def __init__(self, *args, **kwargs):
        super(ArgumentCheckingFTPHost, self).__init__(*args, **kwargs)
        self.path = DummyFTPPath()

    def _make_session(self, *args, **kwargs):
        return DummyFTPSession()

    def mkdir(self, path):
        assert "\\" not in path

    def open(self, path, mode):
        assert "\\" not in path
        return io.StringIO("")


class TestUploadFromWindows(unittest.TestCase):

    def test_no_mixed_separators(self):
        source = LocalWindowsHost()
        target = ArgumentCheckingFTPHost()
        local_root = ntpath.join("some", "directory")
        syncer = ftputil.sync.Syncer(source, target)
        # If the following call raises any `AssertionError`s, the
        # `unittest` framework will catch them and show them.
        syncer.sync(local_root, "not_used_by_ArgumentCheckingFTPHost")


if __name__ == "__main__":
    unittest.main()
