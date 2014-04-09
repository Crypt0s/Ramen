#! /usr/bin/env python
# Copyright (C) 2008-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

# pylint: disable=redefined-builtin

"""\
This script scans a directory tree for files which contain code which
is deprecated or invalid in ftputil %s and above (and even much
longer). The script uses simple heuristics, so it may miss occurences
of deprecated/invalid usage or print some inappropriate lines of your
files.

Usage: %s start_dir

where 'start_dir' is the starting directory which will be scanned
recursively for offending code.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import sys

import ftputil.version


__doc__ = __doc__ % (ftputil.version.__version__,
                     os.path.basename(sys.argv[0]))


class InvalidFeature(object):
    """
    Store message, regex and locations of a single now invalid
    feature.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, message, regex):
        self.message = message
        if not isinstance(regex, re.compile("").__class__):
            regex = re.compile(regex)
        self.regex = regex
        # Map file name to a list of line numbers (starting at 1).
        self.locations = {}


HOST_REGEX = r"\b(h|host|ftp|ftphost|ftp_host)\b"

invalid_features = [
  InvalidFeature("Possible use(s) of FTP exceptions via ftputil module",
                 r"\bftputil\s*?\.\s*?[A-Za-z]+Error\b"),
  InvalidFeature("Possible use(s) of ftp_error module",
                 r"\bftp_error\b"),
  InvalidFeature("Possible use(s) of ftp_stat module",
                 r"\bftp_stat\b"),
  InvalidFeature("Possible use(s) of FTPHost.file",
                 r"{0}\.file\(".format(HOST_REGEX)),
  InvalidFeature("Possible use(s) of FTPHost.open with text mode",
                 r"{0}\.open\(.*[\"'](r|w)t?[\"']".format(HOST_REGEX)),
  InvalidFeature("Possible use(s) of byte string in ignores_line",
                 r"\bdef ignores_line\("),
  InvalidFeature("Possible use(s) of byte string in parse_line",
                 r"\bdef parse_line\("),
  InvalidFeature("Possible use(s) download with text mode",
                 r"{0}\.download(_if_newer)?\(".format(HOST_REGEX)),
  InvalidFeature("Possible use(s) upload with text mode",
                 r"{0}\.upload(_if_newer)?\(".format(HOST_REGEX)),
  InvalidFeature("Possible use(s) of xreadline method of FTP file objects",
                 r"\.\s*?xreadlines\b"),
]


def scan_file(file_name):
    """
    Scan a file with name `file_name` for code deprecated in
    ftputil usage and collect the offending data in the dictionary
    `features.locations`.
    """
    with open(file_name) as fobj:
        for index, line in enumerate(fobj, start=1):
            for feature in invalid_features:
                if feature.regex.search(line):
                    locations = feature.locations
                    locations.setdefault(file_name, [])
                    locations[file_name].append((index, line.rstrip()))


def print_results():
    """
    Print statistics of deprecated code after the directory has been
    scanned.
    """
    last_message = ""
    for feature in invalid_features:
        if feature.message != last_message:
            print()
            print(70 * "-")
            print(feature.message, "...")
            print()
            last_message = feature.message
        locations = feature.locations
        if not locations:
            print("   no invalid code found")
            continue
        for file_name in sorted(locations.keys()):
            print(file_name)
            for line_number, line in locations[file_name]:
                print("%5d: %s" % (line_number, line))
    print()
    print("===========================================")
    print("Please check your code also by other means!")
    print("===========================================")


def main(start_dir):
    """
    Scan a directory tree starting at `start_dir` and print uses
    of deprecated features, if any were found.
    """
    # Deliberately shadow global `start_dir`.
    # pylint: disable=redefined-outer-name
    for dir_path, _dirnames, file_names in os.walk(start_dir):
        for file_name in file_names:
            abs_name = os.path.abspath(os.path.join(dir_path, file_name))
            if file_name.endswith(".py"):
                scan_file(abs_name)
    print_results()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        start_dir = sys.argv[1]
        if not os.path.isdir(start_dir):
            print("Directory %s not found." % start_dir, file=sys.stderr)
            sys.exit()
    else:
        print("Usage: %s start_dir" % sys.argv[0], file=sys.stderr)
        sys.exit()
    main(start_dir)
