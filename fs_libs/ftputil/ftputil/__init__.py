# Copyright (C) 2002-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

"""
ftputil - high-level FTP client library

FTPHost objects
    This class resembles the `os` module's interface to ordinary file
    systems. In addition, it provides a method `file` which will
    return file-objects corresponding to remote files.

    # Example session
    with ftputil.FTPHost("ftp.domain.com", "me", "secret") as host:
        print host.getcwd()  # e. g. "/home/me"
        host.mkdir("newdir")
        host.chdir("newdir")
        with host.open("sourcefile", "r") as source:
            with host.open("targetfile", "w") as target:
                host.copyfileobj(source, target)
        host.remove("targetfile")
        host.chdir(host.pardir)
        host.rmdir("newdir")

    There are also shortcuts for uploads and downloads:

    host.upload(local_file, remote_file)
    host.download(remote_file, local_file)

    Both accept an additional mode parameter. If it is "b", the
    transfer mode will be for binary files.

    For even more functionality refer to the documentation in
    `ftputil.txt` or `ftputil.html`.

FTPFile objects
    `FTPFile` objects are constructed via the `file` method (`open`
    is an alias) of `FTPHost` objects. `FTPFile` objects support the
    usual file operations for non-seekable files (`read`, `readline`,
    `readlines`, `write`, `writelines`, `close`).

Note: ftputil currently is not threadsafe. More specifically, you can
      use different `FTPHost` objects in different threads but not
      a single `FTPHost` object in different threads.
"""

from __future__ import absolute_import
from __future__ import unicode_literals

from ftputil.host    import FTPHost
from ftputil.version import __version__


# Apart from `ftputil.error` and `ftputil.stat`, this is the whole
# public API of `ftputil`.
__all__ = ["FTPHost", "__version__"]
