# Copyright (C) 2003-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

from __future__ import unicode_literals

import ftputil

from test import mock_ftplib


# Factory to produce `FTPHost`-like classes from a given `FTPHost`
# class and (usually) a given `MockSession` class.
def ftp_host_factory(session_factory=mock_ftplib.MockUnixFormatSession,
                     ftp_host_class=ftputil.FTPHost):
    return ftp_host_class("dummy_host", "dummy_user", "dummy_password",
                          session_factory=session_factory)
