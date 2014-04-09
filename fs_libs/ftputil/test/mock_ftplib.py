# encoding: utf-8
# Copyright (C) 2003-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

"""
This module implements a mock version of the standard library's
`ftplib.py` module. Some code is taken from there.

Not all functionality is implemented, only what is needed to run the
unit tests.
"""

from __future__ import unicode_literals

import io
import collections
import ftplib
import posixpath

import ftputil.tool


DEBUG = 0

# Use a global dictionary of the form `{path: `MockFile` object, ...}`
# to make "remote" mock files that were generated during a test
# accessible. For example, this is used for testing the contents of a
# file after an `FTPHost.upload` call.
mock_files = {}

def content_of(path):
    """
    Return the data stored in a mock remote file identified by `path`.
    """
    return mock_files[path].getvalue()


class MockFile(io.BytesIO, object):
    """
    Mock class for the file objects _contained in_ `FTPFile` objects
    (not `FTPFile` objects themselves!).

    Contrary to `StringIO.StringIO` instances, `MockFile` objects can
    be queried for their contents after they have been closed.
    """

    def __init__(self, path, content=b""):
        global mock_files
        mock_files[path] = self
        self._value_after_close = ""
        self._super = super(MockFile, self)
        self._super.__init__(content)

    def getvalue(self):
        if not self.closed:
            return self._super.getvalue()
        else:
            return self._value_after_close

    def close(self):
        if not self.closed:
            self._value_after_close = self._super.getvalue()
        self._super.close()


class MockSocket(object):
    """
    Mock class which is used to return something from
    `MockSession.transfercmd`.
    """
    def __init__(self, path, mock_file_content=b""):
        if DEBUG:
            print("File content: *{0}*".format(mock_file_content))
        self.file_path = path
        self.mock_file_content = mock_file_content
        self._timeout = 60

    def makefile(self, mode):
        return MockFile(self.file_path, self.mock_file_content)

    def close(self):
        pass

    # Timeout-related methods are used in `FTPFile.close`.
    def gettimeout(self):
        return self._timeout

    def settimeout(self, timeout):
        self._timeout = timeout


class MockSession(object):
    """
    Mock class which works like `ftplib.FTP` for the purpose of the
    unit tests.
    """
    # Used by `MockSession.cwd` and `MockSession.pwd`
    current_dir = "/home/sschwarzer"

    # Used by `MockSession.dir`. This is a mapping from absolute path
    # to the multi-line string that would show up in an FTP
    # command-line client for this directory.
    dir_contents = {}

    # File content to be used (indirectly) with `transfercmd`.
    mock_file_content = b""

    def __init__(self, host="", user="", password=""):
        self.closed = 0
        # Copy default from class.
        self.current_dir = self.__class__.current_dir
        # Count successful `transfercmd` invocations to ensure that
        # each has a corresponding `voidresp`.
        self._transfercmds = 0
        # Dummy, only for getting/setting timeout in `FTPFile.close`
        self.sock = MockSocket("", b"")

    def voidcmd(self, cmd):
        if DEBUG:
            print(cmd)
        if cmd == "STAT":
            return "MockSession server awaiting your commands ;-)"
        elif cmd.startswith("TYPE "):
            return
        elif cmd.startswith("SITE CHMOD"):
            raise ftplib.error_perm("502 command not implemented")
        else:
            raise ftplib.error_perm

    def pwd(self):
        return self.current_dir

    def _remove_trailing_slash(self, path):
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return path

    def _transform_path(self, path):
        return posixpath.normpath(posixpath.join(self.pwd(), path))

    def cwd(self, path):
        path = ftputil.tool.as_unicode(path)
        self.current_dir = self._transform_path(path)

    def _ignore_arguments(self, *args, **kwargs):
        pass

    delete = mkd = rename = rmd = _ignore_arguments

    def dir(self, *args):
        """
        Provide a callback function for processing each line of a
        directory listing. Return nothing.
        """
        # The callback comes last in `ftplib.FTP.dir`.
        if isinstance(args[-1], collections.Callable):
            # Get `args[-1]` _before_ removing it in the line after.
            callback = args[-1]
            args = args[:-1]
        else:
            callback = None
        # Everything before the path argument are options.
        path = args[-1]
        if DEBUG:
            print("dir: {0}".format(path))
        path = self._transform_path(path)
        if path not in self.dir_contents:
            raise ftplib.error_perm
        dir_lines = self.dir_contents[path].split("\n")
        for line in dir_lines:
            if callback is None:
                print(line)
            else:
                callback(line)

    def voidresp(self):
        assert self._transfercmds == 1
        self._transfercmds -= 1
        return "2xx"

    def transfercmd(self, cmd):
        """
        Return a `MockSocket` object whose `makefile` method will
        return a mock file object.
        """
        if DEBUG:
            print(cmd)
        # Fail if attempting to read from/write to a directory.
        cmd, path = cmd.split()
        #  Normalize path for lookup.
        path = self._remove_trailing_slash(path)
        if path in self.dir_contents:
            raise ftplib.error_perm
        # Fail if path isn't available (this name is hard-coded here
        # and has to be used for the corresponding tests).
        if (cmd, path) == ("RETR", "notthere"):
            raise ftplib.error_perm
        assert self._transfercmds == 0
        self._transfercmds += 1
        return MockSocket(path, self.mock_file_content)

    def close(self):
        if not self.closed:
            self.closed = 1
            assert self._transfercmds == 0


class MockUnixFormatSession(MockSession):

    dir_contents = {
      "/": """\
drwxr-xr-x   2 45854    200           512 May  4  2000 home""",

      "/home": """\
drwxr-sr-x   2 45854    200           512 May  4  2000 sschwarzer
-rw-r--r--   1 45854    200          4605 Jan 19  1970 older
-rw-r--r--   1 45854    200          4605 Jan 19  2020 newer
lrwxrwxrwx   1 45854    200            21 Jan 19  2002 link -> sschwarzer/index.html
lrwxrwxrwx   1 45854    200            15 Jan 19  2002 bad_link -> python/bad_link
drwxr-sr-x   2 45854    200           512 May  4  2000 dir with spaces
drwxr-sr-x   2 45854    200           512 May  4  2000 file_name_test""",

      "/home/python": """\
lrwxrwxrwx   1 45854    200             7 Jan 19  2002 link_link -> ../link
lrwxrwxrwx   1 45854    200            14 Jan 19  2002 bad_link -> /home/bad_link""",

      "/home/sschwarzer": """\
total 14
drwxr-sr-x   2 45854    200           512 May  4  2000 chemeng
drwxr-sr-x   2 45854    200           512 Jan  3 17:17 download
drwxr-sr-x   2 45854    200           512 Jul 30 17:14 image
-rw-r--r--   1 45854    200          4604 Jan 19 23:11 index.html
drwxr-sr-x   2 45854    200           512 May 29  2000 os2
lrwxrwxrwx   2 45854    200             6 May 29  2000 osup -> ../os2
drwxr-sr-x   2 45854    200           512 May 25  2000 publications
drwxr-sr-x   2 45854    200           512 Jan 20 16:12 python
drwxr-sr-x   6 45854    200           512 Sep 20  1999 scios2""",

      "/home/dir with spaces": """\
total 1
-rw-r--r--   1 45854    200          4604 Jan 19 23:11 file with spaces""",

      "/home/file_name_test": """\
drwxr-sr-x   2 45854    200           512 May 29  2000 ä
drwxr-sr-x   2 45854    200           512 May 29  2000 empty_ä
-rw-r--r--   1 45854    200          4604 Jan 19 23:11 ö
lrwxrwxrwx   2 45854    200             6 May 29  2000 ü -> ä""",

      "/home/file_name_test/ä": """\
-rw-r--r--   1 45854    200          4604 Jan 19 23:11 ö
-rw-r--r--   1 45854    200          4604 Jan 19 23:11 o""",

      "/home/file_name_test/empty_ä": """\
""",
      # Fail when trying to write to this directory (the content isn't
      # relevant).
      "sschwarzer": "",
    }


class MockMSFormatSession(MockSession):

    dir_contents = {
      "/": """\
10-23-01  03:25PM       <DIR>          home""",

      "/home": """\
10-23-01  03:25PM       <DIR>          msformat""",

      "/home/msformat": """\
10-23-01  03:25PM       <DIR>          WindowsXP
12-07-01  02:05PM       <DIR>          XPLaunch
07-17-00  02:08PM             12266720 abcd.exe
07-17-00  02:08PM                89264 O2KKeys.exe""",

      "/home/msformat/XPLaunch": """\
10-23-01  03:25PM       <DIR>          WindowsXP
12-07-01  02:05PM       <DIR>          XPLaunch
12-07-01  02:05PM       <DIR>          empty
07-17-00  02:08PM             12266720 abcd.exe
07-17-00  02:08PM                89264 O2KKeys.exe""",

      "/home/msformat/XPLaunch/empty": "total 0",
    }
