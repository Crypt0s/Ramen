# Copyright (C) 2003-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import stat
import time
import unittest

import ftputil
import ftputil.error
import ftputil.stat

from test import test_base
from test import mock_ftplib


def _test_stat(session_factory):
    host = test_base.ftp_host_factory(session_factory=session_factory)
    stat = ftputil.stat._Stat(host)
    # Use Unix format parser explicitly. This doesn't exclude switching
    # to the MS format parser later if the test allows this switching.
    stat._parser = ftputil.stat.UnixParser()
    return stat


def stat_tuple_to_seconds(t):
    """
    Return a float number representing the local time associated with
    the six-element tuple `t`.
    """
    assert len(t) == 6, \
           "need a six-element tuple (year, month, day, hour, min, sec)"
    return time.mktime(t + (0, 0, -1))


class TestParsers(unittest.TestCase):

    #
    # Helper methods
    #
    def _test_valid_lines(self, parser_class, lines, expected_stat_results):
        parser = parser_class()
        for line, expected_stat_result in zip(lines, expected_stat_results):
            # Convert to list to compare with the list `expected_stat_results`.
            parse_result = parser.parse_line(line)
            stat_result = list(parse_result) + [parse_result._st_name,
                                                parse_result._st_target]
            # Convert time tuple to seconds.
            expected_stat_result[8] = \
              stat_tuple_to_seconds(expected_stat_result[8])
            # Compare lists.
            self.assertEqual(stat_result, expected_stat_result)

    def _test_invalid_lines(self, parser_class, lines):
        parser = parser_class()
        for line in lines:
            self.assertRaises(ftputil.error.ParserError,
                              parser.parse_line, line)

    def _expected_year(self):
        """
        Return the expected year for the second line in the
        listing in `test_valid_unix_lines`.
        """
        # If in this year it's after Dec 19, 23:11, use the current
        # year, else use the previous year. This datetime value
        # corresponds to the hard-coded value in the string lists
        # below.
        now = time.localtime()
        # We need only month, day, hour and minute.
        current_time_parts = now[1:5]
        time_parts_in_listing = (12, 19, 23, 11)
        if current_time_parts > time_parts_in_listing:
            return now[0]
        else:
            return now[0] - 1

    #
    # Unix parser
    #
    def test_valid_unix_lines(self):
        lines = [
          "drwxr-sr-x   2 45854    200           512 May  4  2000 "
            "chemeng link -> chemeng target",
          # The year value for this line will change with the actual time.
          "-rw-r--r--   1 45854    200          4604 Dec 19 23:11 index.html",
          "drwxr-sr-x   2 45854    200           512 May 29  2000 os2",
          "lrwxrwxrwx   2 45854    200           512 May 29  2000 osup -> "
                                                                  "../os2"
          ]
        expected_stat_results = [
          [17901, None, None, 2, "45854", "200", 512, None,
           (2000, 5, 4, 0, 0, 0), None, "chemeng link", "chemeng target"],
          [33188, None, None, 1, "45854", "200", 4604, None,
           (self._expected_year(), 12, 19, 23, 11, 0), None,
           "index.html", None],
          [17901, None, None, 2, "45854", "200", 512, None,
           (2000, 5, 29, 0, 0, 0), None, "os2", None],
          [41471, None, None, 2, "45854", "200", 512, None,
           (2000, 5, 29, 0, 0, 0), None, "osup", "../os2"]
          ]
        self._test_valid_lines(ftputil.stat.UnixParser, lines,
                               expected_stat_results)

    def test_invalid_unix_lines(self):
        lines = [
          # Not intended to be parsed. Should have been filtered out by
          # `ignores_line`.
          "total 14",
          # Invalid month abbreviation
          "drwxr-sr-x   2 45854    200           512 Max  4  2000 chemeng",
          # Incomplete mode
          "drwxr-sr-    2 45854    200           512 May  4  2000 chemeng",
          # Invalid first letter in mode
          "xrwxr-sr-x   2 45854    200           512 May  4  2000 chemeng",
          # Ditto, plus invalid size value
          "xrwxr-sr-x   2 45854    200           51x May  4  2000 chemeng",
          # Is this `os1 -> os2` pointing to `os3`, or `os1` pointing
          # to `os2 -> os3` or the plain name `os1 -> os2 -> os3`? We
          # don't know, so we consider the line invalid.
          "drwxr-sr-x   2 45854    200           512 May 29  2000 "
            "os1 -> os2 -> os3",
          # Missing name
          "-rwxr-sr-x   2 45854    200           51x May  4  2000 ",
          ]
        self._test_invalid_lines(ftputil.stat.UnixParser, lines)

    def test_alternative_unix_format(self):
        # See http://ftputil.sschwarzer.net/trac/ticket/12 for a
        # description for the need for an alternative format.
        lines = [
          "drwxr-sr-x   2   200           512 May  4  2000 "
            "chemeng link -> chemeng target",
          # The year value for this line will change with the actual time.
          "-rw-r--r--   1   200          4604 Dec 19 23:11 index.html",
          "drwxr-sr-x   2   200           512 May 29  2000 os2",
          "lrwxrwxrwx   2   200           512 May 29  2000 osup -> ../os2"
          ]
        expected_stat_results = [
          [17901, None, None, 2, None, "200", 512, None,
           (2000, 5, 4, 0, 0, 0), None, "chemeng link", "chemeng target"],
          [33188, None, None, 1, None, "200", 4604, None,
           (self._expected_year(), 12, 19, 23, 11, 0), None,
           "index.html", None],
          [17901, None, None, 2, None, "200", 512, None,
           (2000, 5, 29, 0, 0, 0), None, "os2", None],
          [41471, None, None, 2, None, "200", 512, None,
           (2000, 5, 29, 0, 0, 0), None, "osup", "../os2"]
          ]
        self._test_valid_lines(ftputil.stat.UnixParser, lines,
                               expected_stat_results)

    #
    # Microsoft parser
    #
    def test_valid_ms_lines_two_digit_year(self):
        lines = [
          "07-27-01  11:16AM       <DIR>          Test",
          "10-23-95  03:25PM       <DIR>          WindowsXP",
          "07-17-00  02:08PM             12266720 test.exe",
          "07-17-09  12:08AM             12266720 test.exe",
          "07-17-09  12:08PM             12266720 test.exe"
          ]
        expected_stat_results = [
          [16640, None, None, None, None, None, None, None,
           (2001, 7, 27, 11, 16, 0), None, "Test", None],
          [16640, None, None, None, None, None, None, None,
           (1995, 10, 23, 15, 25, 0), None, "WindowsXP", None],
          [33024, None, None, None, None, None, 12266720, None,
           (2000, 7, 17, 14, 8, 0), None, "test.exe", None],
          [33024, None, None, None, None, None, 12266720, None,
           (2009, 7, 17, 0, 8, 0), None, "test.exe", None],
          [33024, None, None, None, None, None, 12266720, None,
           (2009, 7, 17, 12, 8, 0), None, "test.exe", None]
          ]
        self._test_valid_lines(ftputil.stat.MSParser, lines,
                               expected_stat_results)

    def test_valid_ms_lines_four_digit_year(self):
        # See http://ftputil.sschwarzer.net/trac/ticket/67
        lines = [
          "10-19-2012  03:13PM       <DIR>          SYNCDEST",
          "10-19-2012  03:13PM       <DIR>          SYNCSOURCE"
          ]
        expected_stat_results = [
          [16640, None, None, None, None, None, None, None,
           (2012, 10, 19, 15, 13, 0), None, "SYNCDEST", None],
          [16640, None, None, None, None, None, None, None,
           (2012, 10, 19, 15, 13, 0), None, "SYNCSOURCE", None],
          ]
        self._test_valid_lines(ftputil.stat.MSParser, lines,
                               expected_stat_results)

    def test_invalid_ms_lines(self):
        lines = [
          # Neither "<DIR>" nor a size present
          "07-27-01  11:16AM                      Test",
          # "AM"/"PM" missing
          "07-17-00  02:08             12266720 test.exe",
          # Invalid size value
          "07-17-00  02:08AM           1226672x test.exe"
          ]
        self._test_invalid_lines(ftputil.stat.MSParser, lines)

    #
    # The following code checks if the decision logic in the Unix
    # line parser for determining the year works.
    #
    def datetime_string(self, time_float):
        """
        Return a datetime string generated from the value in
        `time_float`. The parameter value is a floating point value
        as returned by `time.time()`. The returned string is built as
        if it were from a Unix FTP server (format: MMM dd hh:mm")
        """
        time_tuple = time.localtime(time_float)
        return time.strftime("%b %d %H:%M", time_tuple)

    def dir_line(self, time_float):
        """
        Return a directory line as from a Unix FTP server. Most of
        the contents are fixed, but the timestamp is made from
        `time_float` (seconds since the epoch, as from `time.time()`).
        """
        line_template = \
          "-rw-r--r--   1   45854   200   4604   {0}   index.html"
        return line_template.format(self.datetime_string(time_float))

    def assert_equal_times(self, time1, time2):
        """
        Check if both times (seconds since the epoch) are equal. For
        the purpose of this test, two times are "equal" if they
        differ no more than one minute from each other.
        """
        abs_difference = abs(time1 - time2)
        try:
            self.assertFalse(abs_difference > 60.0)
        except AssertionError:
            print("Difference is", abs_difference, "seconds")
            raise

    def _test_time_shift(self, supposed_time_shift, deviation=0.0):
        """
        Check if the stat parser considers the time shift value
        correctly. `deviation` is the difference between the actual
        time shift and the supposed time shift, which is rounded
        to full hours.
        """
        host = test_base.ftp_host_factory()
        # Explicitly use Unix format parser here.
        host._stat._parser = ftputil.stat.UnixParser()
        host.set_time_shift(supposed_time_shift)
        server_time = time.time() + supposed_time_shift + deviation
        stat_result = host._stat._parser.parse_line(self.dir_line(server_time),
                                                    host.time_shift())
        self.assert_equal_times(stat_result.st_mtime, server_time)

    def test_time_shifts(self):
        """Test correct year depending on time shift value."""
        # 1. test: Client and server share the same local time
        self._test_time_shift(0.0)
        # 2. test: Server is three hours ahead of client
        self._test_time_shift(3 * 60 * 60)
        # 3. test: Client is three hours ahead of server
        self._test_time_shift(- 3 * 60 * 60)
        # 4. test: Server is supposed to be three hours ahead, but
        #    is ahead three hours and one minute
        self._test_time_shift(3 * 60 * 60, 60)
        # 5. test: Server is supposed to be three hours ahead, but
        #    is ahead three hours minus one minute
        self._test_time_shift(3 * 60 * 60, -60)
        # 6. test: Client is supposed to be three hours ahead, but
        #    is ahead three hours and one minute
        self._test_time_shift(-3 * 60 * 60, -60)
        # 7. test: Client is supposed to be three hours ahead, but
        #    is ahead three hours minus one minute
        self._test_time_shift(-3 * 60 * 60, 60)


class TestLstatAndStat(unittest.TestCase):
    """
    Test `FTPHost.lstat` and `FTPHost.stat` (test currently only
    implemented for Unix server format).
    """

    def setUp(self):
        # Most tests in this class need the mock session class with
        # Unix format, so make this the default. Tests which need
        # the MS format can overwrite `self.stat` later.
        self.stat = \
          _test_stat(session_factory=mock_ftplib.MockUnixFormatSession)

    def test_failing_lstat(self):
        """Test whether `lstat` fails for a nonexistent path."""
        self.assertRaises(ftputil.error.PermanentError,
                          self.stat._lstat, "/home/sschw/notthere")
        self.assertRaises(ftputil.error.PermanentError,
                          self.stat._lstat, "/home/sschwarzer/notthere")

    def test_lstat_for_root(self):
        """
        Test `lstat` for `/` .

        Note: `(l)stat` works by going one directory up and parsing
        the output of an FTP `LIST` command. Unfortunately, it's not
        possible to do this for the root directory `/`.
        """
        self.assertRaises(ftputil.error.RootDirError, self.stat._lstat, "/")
        try:
            self.stat._lstat("/")
        except ftputil.error.RootDirError as exc:
            self.assertFalse(isinstance(exc, ftputil.error.FTPOSError))

    def test_lstat_one_unix_file(self):
        """Test `lstat` for a file described in Unix-style format."""
        stat_result = self.stat._lstat("/home/sschwarzer/index.html")
        # Second form is needed for Python 3
        self.assertTrue(oct(stat_result.st_mode) in ("0100644", "0o100644"))
        self.assertEqual(stat_result.st_size, 4604)
        self.assertEqual(stat_result._st_mtime_precision, 60)

    def test_lstat_one_ms_file(self):
        """Test `lstat` for a file described in DOS-style format."""
        self.stat = _test_stat(session_factory=mock_ftplib.MockMSFormatSession)
        stat_result = self.stat._lstat("/home/msformat/abcd.exe")
        self.assertEqual(stat_result._st_mtime_precision, 60)

    def test_lstat_one_unix_dir(self):
        """Test `lstat` for a directory described in Unix-style format."""
        stat_result = self.stat._lstat("/home/sschwarzer/scios2")
        # Second form is needed for Python 3
        self.assertTrue(oct(stat_result.st_mode) in ("042755", "0o42755"))
        self.assertEqual(stat_result.st_ino, None)
        self.assertEqual(stat_result.st_dev, None)
        self.assertEqual(stat_result.st_nlink, 6)
        self.assertEqual(stat_result.st_uid, "45854")
        self.assertEqual(stat_result.st_gid, "200")
        self.assertEqual(stat_result.st_size, 512)
        self.assertEqual(stat_result.st_atime, None)
        self.assertTrue(stat_result.st_mtime ==
                        stat_tuple_to_seconds((1999, 9, 20, 0, 0, 0)))
        self.assertEqual(stat_result.st_ctime, None)
        self.assertEqual(stat_result._st_mtime_precision, 24*60*60)
        self.assertTrue(stat_result ==
          (17901, None, None, 6, "45854", "200", 512, None,
           stat_tuple_to_seconds((1999, 9, 20, 0, 0, 0)), None))

    def test_lstat_one_ms_dir(self):
        """Test `lstat` for a directory described in DOS-style format."""
        self.stat = _test_stat(session_factory=mock_ftplib.MockMSFormatSession)
        stat_result = self.stat._lstat("/home/msformat/WindowsXP")
        self.assertEqual(stat_result._st_mtime_precision, 60)

    def test_lstat_via_stat_module(self):
        """Test `lstat` indirectly via `stat` module."""
        stat_result = self.stat._lstat("/home/sschwarzer/")
        self.assertTrue(stat.S_ISDIR(stat_result.st_mode))

    def test_stat_following_link(self):
        """Test `stat` when invoked on a link."""
        # Simple link
        stat_result = self.stat._stat("/home/link")
        self.assertEqual(stat_result.st_size, 4604)
        # Link pointing to a link
        stat_result = self.stat._stat("/home/python/link_link")
        self.assertEqual(stat_result.st_size, 4604)
        stat_result = self.stat._stat("../python/link_link")
        self.assertEqual(stat_result.st_size, 4604)
        # Recursive link structures
        self.assertRaises(ftputil.error.PermanentError,
                          self.stat._stat, "../python/bad_link")
        self.assertRaises(ftputil.error.PermanentError,
                          self.stat._stat, "/home/bad_link")

    #
    # Test automatic switching of Unix/MS parsers
    #
    def test_parser_switching_with_permanent_error(self):
        """Test non-switching of parser format with `PermanentError`."""
        self.stat = _test_stat(session_factory=mock_ftplib.MockMSFormatSession)
        self.assertEqual(self.stat._allow_parser_switching, True)
        # With these directory contents, we get a `ParserError` for
        # the Unix parser first, so `_allow_parser_switching` can be
        # switched off no matter whether we got a `PermanentError`
        # afterward or not.
        self.assertRaises(ftputil.error.PermanentError,
                          self.stat._lstat, "/home/msformat/nonexistent")
        self.assertEqual(self.stat._allow_parser_switching, False)

    def test_parser_switching_default_to_unix(self):
        """Test non-switching of parser format; stay with Unix."""
        self.assertEqual(self.stat._allow_parser_switching, True)
        self.assertTrue(isinstance(self.stat._parser, ftputil.stat.UnixParser))
        stat_result = self.stat._lstat("/home/sschwarzer/index.html")
        # The Unix parser worked, so keep it.
        self.assertTrue(isinstance(self.stat._parser, ftputil.stat.UnixParser))
        self.assertEqual(self.stat._allow_parser_switching, False)

    def test_parser_switching_to_ms(self):
        """Test switching of parser from Unix to MS format."""
        self.stat = _test_stat(session_factory=mock_ftplib.MockMSFormatSession)
        self.assertEqual(self.stat._allow_parser_switching, True)
        self.assertTrue(isinstance(self.stat._parser, ftputil.stat.UnixParser))
        # Parsing the directory `/home/msformat` with the Unix parser
        # fails, so switch to the MS parser.
        stat_result = self.stat._lstat("/home/msformat/abcd.exe")
        self.assertTrue(isinstance(self.stat._parser, ftputil.stat.MSParser))
        self.assertEqual(self.stat._allow_parser_switching, False)
        self.assertEqual(stat_result._st_name, "abcd.exe")
        self.assertEqual(stat_result.st_size, 12266720)

    def test_parser_switching_regarding_empty_dir(self):
        """Test switching of parser if a directory is empty."""
        self.stat = _test_stat(session_factory=mock_ftplib.MockMSFormatSession)
        self.assertEqual(self.stat._allow_parser_switching, True)
        # When the directory we're looking into doesn't give us any
        # lines we can't decide whether the first parser worked,
        # because it wasn't applied. So keep the parser for now.
        result = self.stat._listdir("/home/msformat/XPLaunch/empty")
        self.assertEqual(result, [])
        self.assertEqual(self.stat._allow_parser_switching, True)
        self.assertTrue(isinstance(self.stat._parser, ftputil.stat.UnixParser))


class TestListdir(unittest.TestCase):
    """Test `FTPHost.listdir`."""

    def setUp(self):
        self.stat = \
          _test_stat(session_factory=mock_ftplib.MockUnixFormatSession)

    def test_failing_listdir(self):
        """Test failing `FTPHost.listdir`."""
        self.assertRaises(ftputil.error.PermanentError,
                          self.stat._listdir, "notthere")

    def test_succeeding_listdir(self):
        """Test succeeding `FTPHost.listdir`."""
        # Do we have all expected "files"?
        self.assertEqual(len(self.stat._listdir(".")), 9)
        # Have they the expected names?
        expected = ("chemeng download image index.html os2 "
                    "osup publications python scios2").split()
        remote_file_list = self.stat._listdir(".")
        for file in expected:
            self.assertTrue(file in remote_file_list)


if __name__ == "__main__":
    unittest.main()
