# Copyright (C) 2006-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

"""
Provide version information about ftputil and the runtime environment.
"""

from __future__ import unicode_literals

import sys


# ftputil version number; substituted by `make patch`
__version__ = "3.0"

_ftputil_version = __version__
_python_version = sys.version.split()[0]
_python_platform = sys.platform


version_info = "ftputil {0}, Python {1} ({2})".format(
                 _ftputil_version, _python_version, _python_platform)
