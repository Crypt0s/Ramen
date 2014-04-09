# encoding: UTF-8

# Copyright (C) 2003-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

# Execute tests on a real FTP server (other tests use a mock server).

from __future__ import absolute_import
from __future__ import unicode_literals

import ftplib
import functools
import gc
import operator
import os
import time
import unittest
import stat

import ftputil.compat
import ftputil.error
import ftputil.file_transfer
import ftputil.stat_cache

import test


def utc_local_time_shift():
    """
    Return the expected time shift in seconds assuming the server
    uses UTC in its listings and the client uses local time.

    This is needed because Pure-FTPd meanwhile seems to insist that
    the displayed time for files is in UTC.
    """
    utc_tuple = time.gmtime()
    localtime_tuple = time.localtime()
    # To calculate the correct times shift, we need to ignore the
    # DST component in the localtime tuple, i. e. set it to 0.
    localtime_tuple = localtime_tuple[:-1] + (0,)
    time_shift_in_seconds = (time.mktime(utc_tuple) -
                             time.mktime(localtime_tuple))
    # To be safe, round the above value to units of 3600 s (1 hour).
    return round(time_shift_in_seconds / 3600.0) * 3600

# Difference between local times of server and client. If 0.0, server
# and client use the same timezone.
#EXPECTED_TIME_SHIFT = utc_local_time_shift()
# Pure-FTPd seems to have changed its mind (see docstring of
# `utc_local_time_shift`).
EXPECTED_TIME_SHIFT = 0.0


class Cleaner(object):
    """
    This class helps remove directories and files which might
    otherwise be left behind if a test fails in unexpected ways.
    """

    def __init__(self, host):
        # The test class (probably `RealFTPTest`) and the helper
        # class share the same `FTPHost` object.
        self._host = host
        self._ftp_items = []

    def add_dir(self, path):
        """Schedule a directory with path `path` for removal."""
        self._ftp_items.append(("d", self._host.path.abspath(path)))

    def add_file(self, path):
        """Schedule a file with path `path` for removal."""
        self._ftp_items.append(("f", self._host.path.abspath(path)))

    def clean(self):
        """
        Remove the directories and files previously remembered.
        The removal works in reverse order of the scheduling with
        `add_dir` and `add_file`.

        Errors due to a removal are ignored.
        """
        self._host.chdir("/")
        for type_, path in reversed(self._ftp_items):
            try:
                if type_ == "d":
                    # If something goes wrong in `rmtree` we might
                    # leave a mess behind.
                    self._host.rmtree(path)
                elif type_ == "f":
                    # Minor mess if `remove` fails
                    self._host.remove(path)
            except ftputil.error.FTPError:
                pass


class RealFTPTest(unittest.TestCase):

    def setUp(self):
        # Server, username, password.
        self.login_data = ("localhost", "ftptest",
                            "d605581757de5eb56d568a4419f4126e")
        self.host = ftputil.FTPHost(*self.login_data)
        self.cleaner = Cleaner(self.host)

    def tearDown(self):
        self.cleaner.clean()
        self.host.close()

    #
    # Helper methods
    #
    def make_remote_file(self, path):
        """Create a file on the FTP host."""
        self.cleaner.add_file(path)
        with self.host.open(path, "wb") as file_:
            # Write something. Otherwise the FTP server might not update
            # the time of last modification if the file existed before.
            file_.write(b"\n")

    def make_local_file(self):
        """Create a file on the local host (= on the client side)."""
        with open("_local_file_", "wb") as fobj:
            fobj.write(b"abc\x12\x34def\t")


class TestMkdir(RealFTPTest):

    def test_mkdir_rmdir(self):
        host = self.host
        dir_name = "_testdir_"
        file_name = host.path.join(dir_name, "_nonempty_")
        self.cleaner.add_dir(dir_name)
        # Make dir and check if the directory is there.
        host.mkdir(dir_name)
        files = host.listdir(host.curdir)
        self.assertTrue(dir_name in files)
        # Try to remove a non-empty directory.
        self.cleaner.add_file(file_name)
        non_empty = host.open(file_name, "w")
        non_empty.close()
        self.assertRaises(ftputil.error.PermanentError, host.rmdir, dir_name)
        # Remove file.
        host.unlink(file_name)
        # `remove` on a directory should fail.
        try:
            try:
                host.remove(dir_name)
            except ftputil.error.PermanentError as exc:
                self.assertTrue(str(exc).startswith(
                                "remove/unlink can only delete files"))
            else:
                self.assertTrue(False, "we shouldn't have come here")
        finally:
            # Delete empty directory.
            host.rmdir(dir_name)
        files = host.listdir(host.curdir)
        self.assertTrue(dir_name not in files)

    def test_makedirs_without_existing_dirs(self):
        host = self.host
        # No `_dir1_` yet
        self.assertFalse("_dir1_" in host.listdir(host.curdir))
        # Vanilla case, all should go well.
        host.makedirs("_dir1_/dir2/dir3/dir4")
        self.cleaner.add_dir("_dir1_")
        # Check host.
        self.assertTrue(host.path.isdir("_dir1_"))
        self.assertTrue(host.path.isdir("_dir1_/dir2"))
        self.assertTrue(host.path.isdir("_dir1_/dir2/dir3"))
        self.assertTrue(host.path.isdir("_dir1_/dir2/dir3/dir4"))

    def test_makedirs_from_non_root_directory(self):
        # This is a testcase for issue #22, see
        # http://ftputil.sschwarzer.net/trac/ticket/22 .
        host = self.host
        # No `_dir1_` and `_dir2_` yet
        self.assertFalse("_dir1_" in host.listdir(host.curdir))
        self.assertFalse("_dir2_" in host.listdir(host.curdir))
        # Part 1: Try to make directories starting from `_dir1_` and
        # change to non-root directory.
        self.cleaner.add_dir("_dir1_")
        host.mkdir("_dir1_")
        host.chdir("_dir1_")
        host.makedirs("_dir2_/_dir3_")
        # Test for expected directory hierarchy.
        self.assertTrue (host.path.isdir("/_dir1_"))
        self.assertTrue (host.path.isdir("/_dir1_/_dir2_"))
        self.assertTrue (host.path.isdir("/_dir1_/_dir2_/_dir3_"))
        self.assertFalse(host.path.isdir("/_dir1_/_dir1_"))
        # Remove all but the directory we're in.
        host.rmdir("/_dir1_/_dir2_/_dir3_")
        host.rmdir("/_dir1_/_dir2_")
        # Part 2: Try to make directories starting from root.
        self.cleaner.add_dir("/_dir2_")
        host.makedirs("/_dir2_/_dir3_")
        # Test for expected directory hierarchy
        self.assertTrue (host.path.isdir("/_dir2_"))
        self.assertTrue (host.path.isdir("/_dir2_/_dir3_"))
        self.assertFalse(host.path.isdir("/_dir1_/_dir2_"))

    def test_makedirs_of_existing_directory(self):
        host = self.host
        # The (chrooted) login directory
        host.makedirs("/")

    def test_makedirs_with_file_in_the_way(self):
        host = self.host
        self.cleaner.add_dir("_dir1_")
        host.mkdir("_dir1_")
        self.make_remote_file("_dir1_/file1")
        # Try it.
        self.assertRaises(ftputil.error.PermanentError,
                          host.makedirs, "_dir1_/file1")
        self.assertRaises(ftputil.error.PermanentError,
                          host.makedirs, "_dir1_/file1/dir2")

    def test_makedirs_with_existing_directory(self):
        host = self.host
        self.cleaner.add_dir("_dir1_")
        host.mkdir("_dir1_")
        host.makedirs("_dir1_/dir2")
        # Check
        self.assertTrue(host.path.isdir("_dir1_"))
        self.assertTrue(host.path.isdir("_dir1_/dir2"))

    def test_makedirs_in_non_writable_directory(self):
        host = self.host
        # Preparation: `rootdir1` exists but is only writable by root.
        self.assertRaises(ftputil.error.PermanentError, host.makedirs,
                          "rootdir1/dir2")

    def test_makedirs_with_writable_directory_at_end(self):
        host = self.host
        self.cleaner.add_dir("rootdir2/dir2")
        # Preparation: `rootdir2` exists but is only writable by root.
        # `dir2` is writable by regular ftp user. These both should work.
        host.makedirs("rootdir2/dir2")
        host.makedirs("rootdir2/dir2/dir3")


class TestRemoval(RealFTPTest):

    def test_rmtree_without_error_handler(self):
        host = self.host
        # Build a tree.
        self.cleaner.add_dir("_dir1_")
        host.makedirs("_dir1_/dir2")
        self.make_remote_file("_dir1_/file1")
        self.make_remote_file("_dir1_/file2")
        self.make_remote_file("_dir1_/dir2/file3")
        self.make_remote_file("_dir1_/dir2/file4")
        # Try to remove a _file_ with `rmtree`.
        self.assertRaises(ftputil.error.PermanentError, host.rmtree,
                          "_dir1_/file2")
        # Remove `dir2`.
        host.rmtree("_dir1_/dir2")
        self.assertFalse(host.path.exists("_dir1_/dir2"))
        self.assertTrue (host.path.exists("_dir1_/file2"))
        # Re-create `dir2` and remove `_dir1_`.
        host.mkdir("_dir1_/dir2")
        self.make_remote_file("_dir1_/dir2/file3")
        self.make_remote_file("_dir1_/dir2/file4")
        host.rmtree("_dir1_")
        self.assertFalse(host.path.exists("_dir1_"))

    def test_rmtree_with_error_handler(self):
        host = self.host
        self.cleaner.add_dir("_dir1_")
        host.mkdir("_dir1_")
        self.make_remote_file("_dir1_/file1")
        # Prepare error "handler"
        log = []
        def error_handler(*args):
            log.append(args)
        # Try to remove a file as root "directory".
        host.rmtree("_dir1_/file1", ignore_errors=True, onerror=error_handler)
        self.assertEqual(log, [])
        host.rmtree("_dir1_/file1", ignore_errors=False, onerror=error_handler)
        self.assertEqual(log[0][0], host.listdir)
        self.assertEqual(log[0][1], "_dir1_/file1")
        self.assertEqual(log[1][0], host.rmdir)
        self.assertEqual(log[1][1], "_dir1_/file1")
        host.rmtree("_dir1_")
        # Try to remove a non-existent directory.
        del log[:]
        host.rmtree("_dir1_", ignore_errors=False, onerror=error_handler)
        self.assertEqual(log[0][0], host.listdir)
        self.assertEqual(log[0][1], "_dir1_")
        self.assertEqual(log[1][0], host.rmdir)
        self.assertEqual(log[1][1], "_dir1_")

    def test_remove_non_existent_item(self):
        host = self.host
        self.assertRaises(ftputil.error.PermanentError, host.remove,
                          "nonexistent")

    def test_remove_existing_file(self):
        self.cleaner.add_file("_testfile_")
        self.make_remote_file("_testfile_")
        host = self.host
        self.assertTrue(host.path.isfile("_testfile_"))
        host.remove("_testfile_")
        self.assertFalse(host.path.exists("_testfile_"))


class TestWalk(RealFTPTest):

    def test_walk_topdown(self):
        # Preparation: build tree in directory `walk_test`.
        host = self.host
        expected = [
          ("walk_test",
           ["dir1", "dir2", "dir3"],
           ["file4"]),

          ("walk_test/dir1",
           ["dir11", "dir12"],
           []),

          ("walk_test/dir1/dir11",
           [],
           []),

          ("walk_test/dir1/dir12",
           ["dir123"],
           ["file121", "file122"]),

          ("walk_test/dir1/dir12/dir123",
           [],
           ["file1234"]),

          ("walk_test/dir2",
           [],
           []),

          ("walk_test/dir3",
           ["dir33"],
           ["file31", "file32"]),

          ("walk_test/dir3/dir33",
           [],
           []),
          ]
        # Collect data using `walk`.
        actual = []
        for items in host.walk("walk_test"):
            actual.append(items)
        # Compare with expected results.
        self.assertEqual(len(actual), len(expected))
        for index, _ in enumerate(actual):
            self.assertEqual(actual[index], expected[index])

    def test_walk_depth_first(self):
        # Preparation: build tree in directory `walk_test`
        host = self.host
        expected = [
          ("walk_test/dir1/dir11",
           [],
           []),

          ("walk_test/dir1/dir12/dir123",
           [],
           ["file1234"]),

          ("walk_test/dir1/dir12",
           ["dir123"],
           ["file121", "file122"]),

          ("walk_test/dir1",
           ["dir11", "dir12"],
           []),

          ("walk_test/dir2",
           [],
           []),

          ("walk_test/dir3/dir33",
           [],
           []),

          ("walk_test/dir3",
           ["dir33"],
           ["file31", "file32"]),

          ("walk_test",
           ["dir1", "dir2", "dir3"],
           ["file4"])
          ]
        # Collect data using `walk`.
        actual = []
        for items in host.walk("walk_test", topdown=False):
            actual.append(items)
        # Compare with expected results.
        self.assertEqual(len(actual), len(expected))
        for index, _ in enumerate(actual):
            self.assertEqual(actual[index], expected[index])


class TestRename(RealFTPTest):

    def test_rename(self):
        host = self.host
        # Make sure the target of the renaming operation is removed.
        self.cleaner.add_file("_testfile2_")
        self.make_remote_file("_testfile1_")
        host.rename("_testfile1_", "_testfile2_")
        self.assertFalse(host.path.exists("_testfile1_"))
        self.assertTrue (host.path.exists("_testfile2_"))

    def test_rename_with_spaces_in_directory(self):
        host = self.host
        dir_name = "_dir with spaces_"
        self.cleaner.add_dir(dir_name)
        host.mkdir(dir_name)
        self.make_remote_file(dir_name + "/testfile1")
        host.rename(dir_name + "/testfile1", dir_name + "/testfile2")
        self.assertFalse(host.path.exists(dir_name + "/testfile1"))
        self.assertTrue (host.path.exists(dir_name + "/testfile2"))


class TestStat(RealFTPTest):

    def test_stat(self):
        host = self.host
        dir_name = "_testdir_"
        file_name = host.path.join(dir_name, "_nonempty_")
        # Make a directory and a file in it.
        self.cleaner.add_dir(dir_name)
        host.mkdir(dir_name)
        with host.open(file_name, "wb") as fobj:
            fobj.write(b"abc\x12\x34def\t")
        # Do some stats
        # - dir
        dir_stat = host.stat(dir_name)
        self.assertTrue(isinstance(dir_stat._st_name,
                                   ftputil.compat.unicode_type))
        self.assertEqual(host.listdir(dir_name), ["_nonempty_"])
        self.assertTrue (host.path.isdir (dir_name))
        self.assertFalse(host.path.isfile(dir_name))
        self.assertFalse(host.path.islink(dir_name))
        # - file
        file_stat = host.stat(file_name)
        self.assertTrue(isinstance(file_stat._st_name,
                                   ftputil.compat.unicode_type))
        self.assertFalse(host.path.isdir (file_name))
        self.assertTrue (host.path.isfile(file_name))
        self.assertFalse(host.path.islink(file_name))
        self.assertEqual(host.path.getsize(file_name), 9)
        # - file's modification time; allow up to two minutes difference
        host.synchronize_times()
        server_mtime = host.path.getmtime(file_name)
        client_mtime = time.mktime(time.localtime())
        calculated_time_shift = server_mtime - client_mtime
        self.assertFalse(abs(calculated_time_shift-host.time_shift()) > 120)

    def test_issomething_for_nonexistent_directory(self):
        host = self.host
        # Check if we get the right results if even the containing
        # directory doesn't exist (see ticket #66).
        nonexistent_path = "/nonexistent/nonexistent"
        self.assertFalse(host.path.isdir (nonexistent_path))
        self.assertFalse(host.path.isfile(nonexistent_path))
        self.assertFalse(host.path.islink(nonexistent_path))

    def test_special_broken_link(self):
        # Test for ticket #39.
        host = self.host
        broken_link_name = os.path.join("dir_with_broken_link", "nonexistent")
        self.assertEqual(host.lstat(broken_link_name)._st_target,
                         "../nonexistent/nonexistent")
        self.assertFalse(host.path.isdir (broken_link_name))
        self.assertFalse(host.path.isfile(broken_link_name))
        self.assertTrue (host.path.islink(broken_link_name))

    def test_concurrent_access(self):
        self.make_remote_file("_testfile_")
        with ftputil.FTPHost(*self.login_data) as host1:
            with ftputil.FTPHost(*self.login_data) as host2:
                stat_result1 = host1.stat("_testfile_")
                stat_result2 = host2.stat("_testfile_")
                self.assertEqual(stat_result1, stat_result2)
                host2.remove("_testfile_")
                # Can still get the result via `host1`
                stat_result1 = host1.stat("_testfile_")
                self.assertEqual(stat_result1, stat_result2)
                # Stat'ing on `host2` gives an exception.
                self.assertRaises(ftputil.error.PermanentError,
                                  host2.stat, "_testfile_")
                # Stat'ing on `host1` after invalidation
                absolute_path = host1.path.join(host1.getcwd(), "_testfile_")
                host1.stat_cache.invalidate(absolute_path)
                self.assertRaises(ftputil.error.PermanentError,
                                  host1.stat, "_testfile_")

    def test_cache_auto_resizing(self):
        """Test if the cache is resized appropriately."""
        host = self.host
        cache = host.stat_cache._cache
        # Make sure the cache size isn't adjusted towards smaller values.
        unused_entries = host.listdir("walk_test")
        self.assertEqual(cache.size,
                         ftputil.stat_cache.StatCache._DEFAULT_CACHE_SIZE)
        # Make the cache very small initially and see if it gets resized.
        cache.size = 2
        entries = host.listdir("walk_test")
        # The adjusted cache size should be larger or equal to the
        # number of items in `walk_test` and its parent directory. The
        # latter is read implicitly upon `listdir`'s `isdir` call.
        expected_min_cache_size = max(len(host.listdir(host.curdir)),
                                      len(entries))
        self.assertTrue(cache.size >= expected_min_cache_size)


class TestUploadAndDownload(RealFTPTest):
    """Test upload and download (including time shift test)."""

    def test_time_shift(self):
        self.host.synchronize_times()
        self.assertEqual(self.host.time_shift(), EXPECTED_TIME_SHIFT)

    @test.skip_long_running_test
    def test_upload(self):
        host = self.host
        host.synchronize_times()
        local_file = "_local_file_"
        remote_file = "_remote_file_"
        # Make local file to upload.
        self.make_local_file()
        # Wait, else small time differences between client and server
        # actually could trigger the update.
        time.sleep(65)
        try:
            self.cleaner.add_file(remote_file)
            host.upload(local_file, remote_file)
            # Retry; shouldn't be uploaded
            uploaded = host.upload_if_newer(local_file, remote_file)
            self.assertEqual(uploaded, False)
            # Rewrite the local file.
            self.make_local_file()
            # Retry; should be uploaded now
            uploaded = host.upload_if_newer(local_file, remote_file)
            self.assertEqual(uploaded, True)
        finally:
            # Clean up
            os.unlink(local_file)

    @test.skip_long_running_test
    def test_download(self):
        host = self.host
        host.synchronize_times()
        local_file = "_local_file_"
        remote_file = "_remote_file_"
        # Make a remote file.
        self.make_remote_file(remote_file)
        # File should be downloaded as it's not present yet.
        downloaded = host.download_if_newer(remote_file, local_file)
        self.assertEqual(downloaded, True)
        try:
            # If the remote file, taking the datetime precision into
            # account, _might_ be newer, the file will be downloaded
            # again. To prevent this, wait a bit over a minute (the
            # remote precision), then "touch" the local file.
            time.sleep(65)
            # Create empty file.
            with open(local_file, "w") as fobj:
                pass
            # Local file is present and newer, so shouldn't download.
            downloaded = host.download_if_newer(remote_file, local_file)
            self.assertEqual(downloaded, False)
            # Re-make the remote file.
            self.make_remote_file(remote_file)
            # Local file is present but possibly older (taking the
            # possible deviation because of the precision into account),
            # so should download.
            downloaded = host.download_if_newer(remote_file, local_file)
            self.assertEqual(downloaded, True)
        finally:
            # Clean up.
            os.unlink(local_file)

    def test_callback_with_transfer(self):
        host = self.host
        FILE_NAME = "debian-keyring.tar.gz"
        # Default chunk size as in `FTPHost.copyfileobj`
        MAX_COPY_CHUNK_SIZE = ftputil.file_transfer.MAX_COPY_CHUNK_SIZE
        file_size = host.path.getsize(FILE_NAME)
        chunk_count, _ = divmod(file_size, MAX_COPY_CHUNK_SIZE)
        # Add one chunk for remainder.
        chunk_count += 1
        # Define a callback that just collects all data passed to it.
        transferred_chunks_list = []
        def test_callback(chunk):
            transferred_chunks_list.append(chunk)
        try:
            host.download(FILE_NAME, FILE_NAME, callback=test_callback)
            # Construct a list of data chunks we expect.
            expected_chunks_list = []
            with open(FILE_NAME, "rb") as downloaded_fobj:
                while True:
                    chunk = downloaded_fobj.read(MAX_COPY_CHUNK_SIZE)
                    if not chunk:
                        break
                    expected_chunks_list.append(chunk)
            # Examine data collected by callback function.
            self.assertEqual(len(transferred_chunks_list), chunk_count)
            self.assertEqual(transferred_chunks_list, expected_chunks_list)
        finally:
            os.unlink(FILE_NAME)


class TestFTPFiles(RealFTPTest):

    def test_only_closed_children(self):
        REMOTE_FILE_NAME = "debian-keyring.tar.gz"
        host = self.host
        with host.open(REMOTE_FILE_NAME, "rb") as file_obj1:
            # Create empty file and close it.
            with host.open(REMOTE_FILE_NAME, "rb") as file_obj2:
                pass
            # This should re-use the second child because the first isn't
            # closed but the second is.
            with host.open(REMOTE_FILE_NAME, "rb") as file_obj:
                self.assertEqual(len(host._children), 2)
                self.assertTrue(file_obj._host is host._children[1])

    def test_no_timed_out_children(self):
        REMOTE_FILE_NAME = "debian-keyring.tar.gz"
        host = self.host
        # Implicitly create child host object.
        with host.open(REMOTE_FILE_NAME, "rb") as file_obj1:
            pass
        # Monkey-patch file to simulate an FTP server timeout below.
        def timed_out_pwd():
            raise ftplib.error_temp("simulated timeout")
        file_obj1._host._session.pwd = timed_out_pwd
        # Try to get a file - which shouldn't be the timed-out file.
        with host.open(REMOTE_FILE_NAME, "rb") as file_obj2:
            self.assertTrue(file_obj1 is not file_obj2)
        # Re-use closed and not timed-out child session.
        with host.open(REMOTE_FILE_NAME, "rb") as file_obj3:
            pass
        self.assertTrue(file_obj2 is file_obj3)


class TestChmod(RealFTPTest):

    def assert_mode(self, path, expected_mode):
        """
        Return an integer containing the allowed bits in the mode
        change command.

        The `FTPHost` object to test against is `self.host`.
        """
        full_mode = self.host.stat(path).st_mode
        # Remove flags we can't set via `chmod`.
        # Allowed flags according to Python documentation
        # http://docs.python.org/lib/os-file-dir.html .
        allowed_flags = [stat.S_ISUID, stat.S_ISGID, stat.S_ENFMT,
          stat.S_ISVTX, stat.S_IREAD, stat.S_IWRITE, stat.S_IEXEC,
          stat.S_IRWXU, stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
          stat.S_IRWXG, stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
          stat.S_IRWXO, stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]
        allowed_mask = functools.reduce(operator.or_, allowed_flags)
        mode = full_mode & allowed_mask
        self.assertEqual(mode, expected_mode,
                         "mode {0:o} != {1:o}".format(mode, expected_mode))

    def test_chmod_existing_directory(self):
        host = self.host
        host.mkdir("_test dir_")
        self.cleaner.add_dir("_test dir_")
        # Set/get mode of a directory.
        host.chmod("_test dir_", 0o757)
        self.assert_mode("_test dir_", 0o757)
        # Set/get mode in nested directory.
        host.mkdir("_test dir_/nested_dir")
        self.cleaner.add_dir("_test dir_/nested_dir")
        host.chmod("_test dir_/nested_dir", 0o757)
        self.assert_mode("_test dir_/nested_dir", 0o757)

    def test_chmod_existing_file(self):
        host = self.host
        host.mkdir("_test dir_")
        self.cleaner.add_dir("_test dir_")
        # Set/get mode on a file.
        file_name = host.path.join("_test dir_", "_testfile_")
        self.make_remote_file(file_name)
        host.chmod(file_name, 0o646)
        self.assert_mode(file_name, 0o646)

    def test_chmod_nonexistent_path(self):
        # Set/get mode of a non-existing item.
        self.assertRaises(ftputil.error.PermanentError, self.host.chmod,
                          "nonexistent", 0o757)

    def test_cache_invalidation(self):
        host = self.host
        host.mkdir("_test dir_")
        self.cleaner.add_dir("_test dir_")
        # Make sure the mode is in the cache.
        unused_stat_result = host.stat("_test dir_")
        # Set/get mode of the directory.
        host.chmod("_test dir_", 0o757)
        self.assert_mode("_test dir_", 0o757)
        # Set/get mode on a file.
        file_name = host.path.join("_test dir_", "_testfile_")
        self.make_remote_file(file_name)
        # Make sure the mode is in the cache.
        unused_stat_result = host.stat(file_name)
        host.chmod(file_name, 0o646)
        self.assert_mode(file_name, 0o646)


class TestOther(RealFTPTest):

    def test_open_for_reading(self):
        # Test for issues #17 and #51,
        # http://ftputil.sschwarzer.net/trac/ticket/17 and
        # http://ftputil.sschwarzer.net/trac/ticket/51 .
        file1 = self.host.open("debian-keyring.tar.gz", "rb")
        time.sleep(1)
        # Depending on the FTP server, this might return a status code
        # unexpected by `ftplib` or block the socket connection until
        # a server-side timeout.
        file1.close()

    def test_subsequent_reading(self):
        # Opening a file for reading
        with self.host.open("debian-keyring.tar.gz", "rb") as file1:
            pass
        # Make sure that there are no problems if the connection is reused.
        with self.host.open("debian-keyring.tar.gz", "rb") as file2:
            pass
        self.assertTrue(file1._session is file2._session)

    def test_names_with_spaces(self):
        # Test if directories and files with spaces in their names
        # can be used.
        host = self.host
        self.assertTrue(host.path.isdir("dir with spaces"))
        self.assertEqual(host.listdir("dir with spaces"),
                         ["second dir", "some file", "some_file"])
        self.assertTrue(host.path.isdir ("dir with spaces/second dir"))
        self.assertTrue(host.path.isfile("dir with spaces/some_file"))
        self.assertTrue(host.path.isfile("dir with spaces/some file"))

    def test_synchronize_times_without_write_access(self):
        """Test failing synchronization because of non-writable directory."""
        host = self.host
        # This isn't writable by the ftp account the tests are run under.
        host.chdir("rootdir1")
        self.assertRaises(ftputil.error.TimeShiftError, host.synchronize_times)

    def test_bytes_file_name(self):
        """
        Test whether a UTF-8 file name can be sent and retrieved when
        encoded explicitly.
        """
        # This test below would fail under Python 2 and I have no idea
        # how to make it work there without modifying `ftplib`.
        if ftputil.compat.python_version == 2:
            return
        #
        host = self.host
        # This requires an existing file with an UTF-8 encoded name on
        # the remote file system. Note: If the remote file system
        # doesn't use UTF-8, the test will probably succeed anyway.
        FILE_NAME = "_ütf8_file_näme_♯♭_"
        bytes_file_name = FILE_NAME.encode("UTF-8")
        self.cleaner.add_file(bytes_file_name)
        # Write under name `bytes_file_name`
        with host.open(bytes_file_name, "w", encoding="UTF-8") as fobj:
            fobj.write(FILE_NAME)
        # Try to retrieve file with `listdir`.
        items = host.listdir(b".")
        self.assertTrue(bytes_file_name in items)
        #  When getting a directory listing for a unicode directory,
        #  ftputil will implicitly assume the encoding is latin-1 and
        #  won't decode the file name to something different from
        #  `bytes_file_name`.
        items = host.listdir(".")
        self.assertFalse(FILE_NAME in items)
        # Re-open file.
        with host.open(bytes_file_name, "r", encoding="UTF-8") as fobj:
            data = fobj.read()
        # Not the point of this test, but an additional sanity check
        self.assertEqual(data, FILE_NAME)

    def test_list_a_option(self):
        # For this test to pass, the server must _not_ list "hidden"
        # files by default but instead only when the `LIST` `-a`
        # option is used.
        host = self.host
        self.assertTrue(host.use_list_a_option)
        directory_entries = host.listdir(host.curdir)
        self.assertTrue(".hidden" in directory_entries)
        host.use_list_a_option = False
        directory_entries = host.listdir(host.curdir)
        self.assertFalse(".hidden" in directory_entries)

    def _make_objects_to_be_garbage_collected(self):
        for _ in range(10):
            with ftputil.FTPHost(*self.login_data) as host:
                for _ in range(10):
                    unused_stat_result = host.stat("CONTENTS")
                    with host.open("CONTENTS") as fobj:
                        unused_data = fobj.read()

    def test_garbage_collection(self):
        """Test whether there are cycles which prevent garbage collection."""
        gc.collect()
        objects_before_test = len(gc.garbage)
        self._make_objects_to_be_garbage_collected()
        gc.collect()
        objects_after_test = len(gc.garbage)
        self.assertFalse(objects_after_test - objects_before_test)


if __name__ == "__main__":
    print("""\
Test real FTP access.

This test writes some files and directories on the local client and
the remote server. You'll need write access in the login directory.
This test can take a few minutes because it has to wait to test the
timezone calculation.
    """)
    unittest.main()
