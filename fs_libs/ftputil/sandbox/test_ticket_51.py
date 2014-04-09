# Copyright (C) 2010, Stefan Schwarzer
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Test for ftputil ticket #51.
"""

import os
import sys

import ftputil


BASE_NAME = "testdata_"

# to be overwritten later
host = None


def size_to_name(size):
    return "%s%d" % (BASE_NAME, size)


def generate_local_file(size):
    fobj = open(size_to_name(size), "wb")
    fobj.write(size * "x")
    fobj.close()


def upload_file(name):
    host.upload(name, name, "b")


def test_one_file(name):
    print "Testing", name
    sys.stdout.flush()
    fobj = host.open(name, "rb")
    fobj.close()


def clean():
    # local
    local_names = os.listdir(os.curdir)
    for name in local_names:
        if name.startswith(BASE_NAME):
            os.remove(name)
    # remote
    remote_names = host.listdir(host.curdir)
    for name in remote_names:
        if name.startswith(BASE_NAME):
            host.remove(name)

    
def main():
    global host
    host = ftputil.FTPHost("localhost", 'ftptest',
                           'd605581757de5eb56d568a4419f4126e')
    host.stat_cache.resize(102400)
    clean()
    for i in xrange(2**16 + 16):
        # adjust to find a threshold above which `file.close` blocks
        size = i
        generate_local_file(size)
        upload_file(size_to_name(size))
        test_one_file(size_to_name(size))
    clean()


if __name__ == '__main__':
    main()
