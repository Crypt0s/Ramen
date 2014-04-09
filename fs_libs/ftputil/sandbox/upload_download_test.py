#! /usr/bin/env python

# Copyright (C) 2006, Stefan Schwarzer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# - Neither the name of the above author nor the names of the
#   contributors to the software may be used to endorse or promote
#   products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# $Id: upload_download_test.py 633 2006-11-22 22:15:32Z schwa $

# Test script for ticket #13 (reported by Pete Schott)

import getpass
import random
import sys

import ftputil


def login_data():
    """Get host, user, password and return them as a triple."""
    print "Please enter login data:"
    remote_host = raw_input("Remote host: ")
    user = raw_input("User name: ")
    password = getpass.getpass("Password: ")
    print
    #return "localhost", 'ftptest', 'd605581757de5eb56d568a4419f4126e'
    return remote_host, user, password

def test_data():
    """Return a pseudo-random string of length between 0 and 5120."""
    length = random.randint(0, 5120)
    data = [chr(random.randint(0, 255)) for i in range(length)]
    return "".join(data)
    
# open connection and read local data
login_data_ = login_data()
host = ftputil.FTPHost(*login_data_)

# download and test several times
passed = failed = 0
for i in range(500):
    # save and upload random data and try to test remote integrity
    data = test_data()
    local_data_file = open("local_data", "wb")
    local_data_file.write(data)
    local_data_file.close()
    host.upload("local_data", "remote_data", "b")
    # download file and compare it with the expected data
    host.download("remote_data", "local_data", "b")
    local_data_file = open("local_data", "rb")
    local_data = local_data_file.read()
    local_data_file.close()
    print "File %3d (length %4d) is" % ((i+1), len(data)),
    if data == local_data:
        print "ok"
        passed += 1
    else:
        print "NOT OK"
        failed += 1

host.remove("remote_data")
host.close()

print "\n%d tests passed, %d tests failed" % (passed, failed)

