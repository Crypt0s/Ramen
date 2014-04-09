# Copyright (C) 2007-2012, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

"""
Tools for syncing combinations of local and remote directories.

*** WARNING: This is an unfinished in-development version!
"""

# Sync combinations:
# - remote -> local (download)
# - local -> remote (upload)
# - remote -> remote
# - local -> local (maybe implicitly possible due to design, but not targeted)

from __future__ import unicode_literals

import os
import shutil

from ftputil import FTPHost
import ftputil.error

__all__ = ["FTPHost", "LocalHost", "Syncer"]


# Used for copying file objects; value is 64 KB.
CHUNK_SIZE = 64 * 1024


class LocalHost(object):
    """
    Provide an API for local directories and files so we can use the
    same code as for `FTPHost` instances.
    """

    def open(self, path, mode):
        """
        Return a Python file object for file name `path`, opened in
        mode `mode`.
        """
        # This is the built-in `open` function, not `os.open`!
        return open(path, mode)

    def time_shift(self):
        """
        Return the time shift value (see methods `set_time_shift`
        and `time_shift` in class `FTPHost` for a definition). By
        definition, the value is zero for local file systems.
        """
        return 0.0

    def __getattr__(self, attr):
        return getattr(os, attr)


class Syncer(object):
    """
    Control synchronization between combinations of local and remote
    directories and files.
    """

    def __init__(self, source, target):
        """
        Init the `FTPSyncer` instance.

        Each of `source` and `target` is either an `FTPHost` or a
        `LocalHost` object. The source and target directories, resp.
        have to be set with the `chdir` command before passing them
        in. The semantics is so that the items under the source
        directory will show up under the target directory after the
        synchronization (unless there's an error).
        """
        self._source = source
        self._target = target

    def _mkdir(self, target_dir):
        """
        Try to create the target directory `target_dir`. If it already
        exists, don't do anything. If the directory is present but
        it's actually a file, raise a `SyncError`.
        """
        #TODO Handle setting of target mtime according to source mtime
        # (beware of rootdir anomalies; try to handle them as well).
        #print "Making", target_dir
        if self._target.path.isfile(target_dir):
            raise ftputil.error.SyncError(
                  "target dir '{0}' is actually a file".format(target_dir))
        # Deliberately use an `isdir` test instead of `try/except`. The
        #  latter approach might mask other errors we want to see, e. g.
        #  insufficient permissions.
        if not self._target.path.isdir(target_dir):
            self._target.mkdir(target_dir)

    def _sync_file(self, source_file, target_file):
        #XXX This duplicates code from `FTPHost._copyfileobj`. Maybe
        # implement the upload and download methods in terms of
        # `_sync_file`, or maybe not?
        #TODO Handle `IOError`s
        #TODO Handle conditional copy
        #TODO Handle setting of target mtime according to source mtime
        # (beware of rootdir anomalies; try to handle them as well).
        #print "Syncing", source_file, "->", target_file
        source = self._source.open(source_file, "rb")
        try:
            target = self._target.open(target_file, "wb")
            try:
                shutil.copyfileobj(source, target, length=CHUNK_SIZE)
            finally:
                target.close()
        finally:
            source.close()

    def _fix_sep_for_target(self, path):
        """
        Return the string `path` with appropriate path separators for
        the target file system.
        """
        return path.replace(self._source.sep, self._target.sep)

    def _sync_tree(self, source_dir, target_dir):
        """
        Synchronize the source and the target directory tree by
        updating the target to match the source as far as possible.

        Current limitations:
        - _don't_ delete items which are on the target path but not on the
          source path
        - files are always copied, the modification timestamps are not
          compared
        - all files are copied in binary mode, never in ASCII/text mode
        - incomplete error handling
        """
        self._mkdir(target_dir)
        for dirpath, dir_names, file_names in self._source.walk(source_dir):
            for dir_name in dir_names:
                inner_source_dir = self._source.path.join(dirpath, dir_name)
                inner_target_dir = inner_source_dir.replace(source_dir,
                                                            target_dir, 1)
                inner_target_dir = self._fix_sep_for_target(inner_target_dir)
                self._mkdir(inner_target_dir)
            for file_name in file_names:
                source_file = self._source.path.join(dirpath, file_name)
                target_file = source_file.replace(source_dir, target_dir, 1)
                target_file = self._fix_sep_for_target(target_file)
                self._sync_file(source_file, target_file)

    def sync(self, source_path, target_path):
        """
        Synchronize `source_path` and `target_path` (both are strings,
        each denoting a directory or file path), i. e. update the
        target path so that it's a copy of the source path.

        This method handles both directory trees and single files.
        """
        #TODO Handle making of missing intermediate directories
        source_path = self._source.path.abspath(source_path)
        target_path = self._target.path.abspath(target_path)
        if self._source.path.isfile(source_path):
            self._sync_file(source_path, target_path)
        else:
            self._sync_tree(source_path, target_path)
