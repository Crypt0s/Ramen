# Copyright (C) 2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

"""
file_transfer.py - upload, download and generic file copy
"""

from __future__ import unicode_literals

import io
import os


#TODO Think a bit more about the API before making it public.
# # Only `chunks` should be used by clients of the ftputil library. Any
# #  other functionality is supposed to be used via `FTPHost` objects.
# __all__ = ["chunks"]
__all__ = []

# Maximum size of chunk in `FTPHost.copyfileobj` in bytes.
MAX_COPY_CHUNK_SIZE = 64 * 1024


class LocalFile(object):
    """
    Represent a file on the local side which is to be transferred or
    is already transferred.
    """

    def __init__(self, name, mode):
        self.name = os.path.abspath(name)
        self.mode = mode

    def exists(self):
        """
        Return `True` if the path representing this file exists.
        Otherwise return `False`.
        """
        return os.path.exists(self.name)

    def mtime(self):
        """Return the timestamp for the last modification in seconds."""
        return os.path.getmtime(self.name)

    def mtime_precision(self):
        """Return the precision of the last modification time in seconds."""
        # Derived classes might want to use `self`.
        # pylint: disable=no-self-use
        #
        # Assume modification timestamps for local file systems are
        # at least precise up to a second.
        return 1.0

    def fobj(self):
        """Return a file object for the name/path in the constructor."""
        return io.open(self.name, self.mode)


class RemoteFile(object):
    """
    Represent a file on the remote side which is to be transferred or
    is already transferred.
    """

    def __init__(self, ftp_host, name, mode):
        self._host = ftp_host
        self._path = ftp_host.path
        self.name = self._path.abspath(name)
        self.mode = mode

    def exists(self):
        """
        Return `True` if the path representing this file exists.
        Otherwise return `False`.
        """
        return self._path.exists(self.name)

    def mtime(self):
        """Return the timestamp for the last modification in seconds."""
        # Convert to client time zone (see definition of time
        # shift in docstring of `FTPHost.set_time_shift`).
        return self._path.getmtime(self.name) - self._host.time_shift()

    def mtime_precision(self):
        """Return the precision of the last modification time in seconds."""
        # I think using `stat` instead of `lstat` makes more sense here.
        return self._host.stat(self.name)._st_mtime_precision

    def fobj(self):
        """Return a file object for the name/path in the constructor."""
        return self._host.open(self.name, self.mode)


def source_is_newer_than_target(source_file, target_file):
    """
    Return `True` if the source is newer than the target, else `False`.

    Both arguments are `LocalFile` or `RemoteFile` objects.

    It's assumed that the actual modification time is

      reported_mtime <= actual_mtime <= reported_mtime + mtime_precision

    i. e. that the reported mtime is the actual mtime or rounded down
    (truncated).

    For the purpose of this test the source is newer than the target
    if any of the possible actual source modification times is greater
    than the reported target modification time. In other words: If in
    doubt, the file should be transferred.

    This is the only situation where the source is _not_ considered
    newer than the target:

    |/////////////////////|              possible source mtime
                            |////////|   possible target mtime

    That is, the latest possible actual source modification time is
    before the first possible actual target modification time.
    """
    return (source_file.mtime() + source_file.mtime_precision() >=
            target_file.mtime())


def chunks(fobj, max_chunk_size=MAX_COPY_CHUNK_SIZE):
    """
    Return an iterator which yields the contents of the file object.

    For each iteration, at most `max_chunk_size` bytes are read from
    `fobj` and yielded as a byte string. If the file object is
    exhausted, then don't yield any more data but stop the iteration,
    so the client does _not_ get an empty byte string.

    Any exceptions resulting from reading the file object are passed
    through to the client.
    """
    while True:
        chunk = fobj.read(max_chunk_size)
        if not chunk:
            break
        yield chunk


def copyfileobj(source_fobj, target_fobj, max_chunk_size=MAX_COPY_CHUNK_SIZE,
                callback=None):
    """Copy data from file-like object source to file-like object target."""
    # Inspired by `shutil.copyfileobj` (I don't use the `shutil`
    # code directly because it might change)
    for chunk in chunks(source_fobj, max_chunk_size):
        target_fobj.write(chunk)
        if callback is not None:
            callback(chunk)


def copy_file(source_file, target_file, conditional, callback):
    """
    Copy a file from `source_file` to `target_file`.

    These are `LocalFile` or `RemoteFile` objects. Which of them
    is a local or a remote file, respectively, is determined by
    the arguments. If `conditional` is true, the file is only
    copied if the target doesn't exist or is older than the
    source. If `conditional` is false, the file is copied
    unconditionally. Return `True` if the file was copied, else
    `False`.
    """
    if conditional:
        # Evaluate condition: The target file either doesn't exist or is
        # older than the source file. If in doubt (due to imprecise
        # timestamps), perform the transfer.
        transfer_condition = not target_file.exists() or \
          source_is_newer_than_target(source_file, target_file)
        if not transfer_condition:
            # We didn't transfer.
            return False
    source_fobj = source_file.fobj()
    try:
        target_fobj = target_file.fobj()
        try:
            copyfileobj(source_fobj, target_fobj, callback=callback)
        finally:
            target_fobj.close()
    finally:
        source_fobj.close()
    # Transfer accomplished
    return True
