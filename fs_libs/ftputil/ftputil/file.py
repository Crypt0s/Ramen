# Copyright (C) 2003-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# Copyright (C) 2008, Roger Demetrescu <roger.demetrescu@gmail.com>
# See the file LICENSE for licensing terms.

"""
ftputil.file - support for file-like objects on FTP servers
"""

from __future__ import print_function
from __future__ import unicode_literals

import io

import ftputil.compat
import ftputil.error


# This module shouldn't be used by clients of the ftputil library.
__all__ = []


class BufferedIO(io.BufferedIOBase):
    """
    Adapt a file object returned from `socket.makefile` to the
    interfaces of `io.BufferedReader` or `io.BufferedWriter`, so that
    the new object can be wrapped by `io.TextIOWrapper`.

    This is only needed with Python 2, since in Python 3
    `socket.makefile` already returns a `BufferedReader` or
    `BufferedWriter` object (depending on mode).
    """

    def __init__(self, fobj, is_readable=False, is_writable=False):
        # Don't call baseclass constructor for this adapter.
        # pylint: disable=super-init-not-called
        #
        # This is the return value of `socket.makefile` and is already
        # buffered.
        self.raw = fobj
        self._is_readable = is_readable
        self._is_writable = is_writable

    @property
    def closed(self):
        # pylint: disable=missing-docstring
        return self.raw.closed

    def close(self):
        self.raw.close()

    def fileno(self):
        return self.raw.fileno()

    def isatty(self):
        # It's highly unlikely that this file is interactive.
        return False

    def seekable(self):
        return False

    #
    # Interface for `BufferedReader`
    #
    def readable(self):
        return self._is_readable

    def read(self, *arg):
        return self.raw.read(*arg)

    read1 = read

    def readline(self, *arg):
        return self.raw.readline(*arg)

    def readlines(self, *arg):
        return self.raw.readlines(*arg)

    def readinto(self, bytearray_):
        data = self.raw.read(len(bytearray_))
        bytearray_[:len(data)] = data
        return len(data)

    #
    # Interface for `BufferedWriter`
    #
    def writable(self):
        return self._is_writable

    def flush(self):
        self.raw.flush()

    # Derived from `socket.py` in Python 2.6 and 2.7.
    # There doesn't seem to be a public API for this.
    def _write_buffer_size(self):
        """Return current size of the write buffer in bytes."""
        # pylint: disable=protected-access
        if hasattr(self.raw, "_wbuf_len"):
            # Python 2.6.3 - 2.7.5
            return self.raw._wbuf_len
        elif hasattr(self.raw, "_get_wbuf_len"):
            # Python 2.6 - 2.6.2. (Strictly speaking, all other
            # Python 2.6 versions have a `_get_wbuf_len` method, but
            # for 2.6.3 and up it returns `_wbuf_len`).
            return self.raw._get_wbuf_len()
        else:
            # Fallback. In the context of `write` this means the file
            # appears to be unbuffered.
            return 0

    def write(self, bytes_or_bytearray):
        # `BufferedWriter.write` has to return the number of written
        # bytes, but files returned from `socket.makefile` in Python 2
        # return `None`. Hence provide a workaround.
        old_buffer_byte_count = self._write_buffer_size()
        added_byte_count = len(bytes_or_bytearray)
        self.raw.write(bytes_or_bytearray)
        new_buffer_byte_count = self._write_buffer_size()
        return (old_buffer_byte_count + added_byte_count -
                new_buffer_byte_count)

    def writelines(self, lines):
        self.raw.writelines(lines)


class FTPFile(object):
    """
    Represents a file-like object associated with an FTP host. File
    and socket are closed appropriately if the `close` method is
    called.
    """

    # Set timeout in seconds when closing file connections (see ticket #51).
    _close_timeout = 5

    def __init__(self, host):
        """Construct the file(-like) object."""
        self._host = host
        # pylint: disable=protected-access
        self._session = host._session
        # The file is still closed.
        self.closed = True
        self._conn = None
        self._fobj = None

    def _open(self, path, mode, buffering=None, encoding=None, errors=None,
              newline=None):
        """
        Open the remote file with given path name and mode.

        Contrary to the `open` builtin, this method returns `None`,
        instead this file object is modified in-place.
        """
        # We use the same arguments as in `io.open`.
        # pylint: disable=too-many-arguments
        #
        # `buffering` argument isn't used at this time.
        # pylint: disable=unused-argument
        #
        # Python 3's `socket.makefile` supports the same interface as
        # the new `open` builtin, but Python 2 supports only a mode,
        # but doesn't return an object with the proper interface to
        # wrap it in `io.TextIOWrapper`.
        #
        # Therefore, to make the code work on Python 2 _and_ 3, use
        # `socket.makefile` to always create a binary file and under
        # Python 2 wrap it in an adapter class.
        #
        # Check mode.
        if "a" in mode:
            raise ftputil.error.FTPIOError("append mode not supported")
        if mode not in ("r", "rb", "rt", "w", "wb", "wt"):
            raise ftputil.error.FTPIOError("invalid mode '{0}'".format(mode))
        if "b" in mode and "t" in mode:
            # Raise a `ValueError` like Python would.
            raise ValueError("can't have text and binary mode at once")
        # Convenience variables
        is_binary_mode = "b" in mode
        is_read_mode = "r" in mode
        # Always use binary mode (see above).
        transfer_type = "I"
        command = "TYPE {0}".format(transfer_type)
        with ftputil.error.ftplib_error_to_ftp_io_error:
            self._session.voidcmd(command)
        # Make transfer command.
        command_type = ("STOR", "RETR")[is_read_mode]
        command = "{0} {1}".format(command_type, path)
        # Force to binary regardless of transfer type (see above).
        makefile_mode = mode
        makefile_mode = makefile_mode.replace("t", "")
        if not "b" in makefile_mode:
            makefile_mode += "b"
        # Get connection and file object.
        with ftputil.error.ftplib_error_to_ftp_io_error:
            self._conn = self._session.transfercmd(command)
        # The file object. Under Python 3, this will already be a
        # `BufferedReader` or `BufferedWriter` object.
        fobj = self._conn.makefile(makefile_mode)
        if ftputil.compat.python_version == 2:
            if is_read_mode:
                fobj = BufferedIO(fobj, is_readable=True)
            else:
                fobj = BufferedIO(fobj, is_writable=True)
        if not is_binary_mode:
            fobj = io.TextIOWrapper(fobj, encoding=encoding,
                                    errors=errors, newline=newline)
        self._fobj = fobj
        # This comes last so that `close` won't try to close `FTPFile`
        # objects without `_conn` and `_fobj` attributes in case of an
        # error.
        self.closed = False

    def __iter__(self):
        """Return a file iterator."""
        return self

    def __next__(self):
        """
        Return the next line or raise `StopIteration`, if there are
        no more.
        """
        # Apply implicit line ending conversion for text files.
        line = self.readline()
        if line:
            return line
        else:
            raise StopIteration

    # Although Python 2.6+ has the `next` builtin function already, it
    # still requires iterators to have a `next` method.
    next = __next__

    #
    # Context manager methods
    #
    def __enter__(self):
        # Return `self`, so it can be accessed as the variable
        # component of the `with` statement.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We don't need the `exc_*` arguments here
        # pylint: disable=unused-argument
        self.close()
        # Be explicit
        return False

    #
    # Other attributes
    #
    def __getattr__(self, attr_name):
        """
        Handle requests for attributes unknown to `FTPFile` objects:
        delegate the requests to the contained file object.
        """
        if attr_name in ("encoding flush isatty fileno read readline "
                         "readlines seek tell truncate name softspace "
                         "write writelines".split()):
            return getattr(self._fobj, attr_name)
        raise AttributeError(
                "'FTPFile' object has no attribute '{0}'".format(attr_name))

    # TODO: Implement `__dir__`? (See
    # http://docs.python.org/py3k/whatsnew/2.6.html#other-language-changes )

    def close(self):
        """Close the `FTPFile`."""
        if self.closed:
            return
        # Timeout value to restore, see below.
        # Statement works only before the try/finally statement,
        # otherwise Python raises an `UnboundLocalError`.
        old_timeout = self._session.sock.gettimeout()
        try:
            self._fobj.close()
            self._fobj = None
            with ftputil.error.ftplib_error_to_ftp_io_error:
                self._conn.close()
            # Set a timeout to prevent waiting until server timeout
            # if we have a server blocking here like in ticket #51.
            self._session.sock.settimeout(self._close_timeout)
            try:
                with ftputil.error.ftplib_error_to_ftp_io_error:
                    self._session.voidresp()
            except ftputil.error.FTPIOError as exc:
                # Ignore some errors, see tickets #51 and #17 at
                # http://ftputil.sschwarzer.net/trac/ticket/51 and
                # http://ftputil.sschwarzer.net/trac/ticket/17,
                # respectively.
                exc = str(exc)
                error_code = exc[:3]
                if exc.splitlines()[0] != "timed out" and \
                  error_code not in ("150", "426", "450", "451"):
                    raise
        finally:
            # Restore timeout for socket of `FTPFile`'s `ftplib.FTP`
            # object in case the connection is reused later.
            self._session.sock.settimeout(old_timeout)
            # If something went wrong before, the file is probably
            # defunct and subsequent calls to `close` won't help
            # either, so we consider the file closed for practical
            # purposes.
            self.closed = True
