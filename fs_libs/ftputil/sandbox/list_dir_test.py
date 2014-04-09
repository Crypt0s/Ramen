#! /usr/bin/env python
# coding: iso-8859-1

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

# $Id: $

# use experimental ftputil version
import sys
sys.path.insert(0, "/home/schwa/sd/python/ftputil.add_stat_caching")

import ftputil


def main():
    test_dir = "pub/FreeBSD/doc"
    ftp_host = ftputil.FTPHost("ftp.de.freebsd.org", 'anonymous',
                               "sschwarzer@sschwarzer.net")
    def onerror(err):
        print err
    for top, dirs, nondirs in ftp_host.walk(test_dir, onerror=onerror):
        print top
        print "  ", dirs
        print "  ", nondirs
        print
        if top == "pub/FreeBSD/doc/fr_FR.ISO8859-1/books/ppp-primer":
            break
    print "Stat cache:"
    #print ftp_host.stat_cache
    print len(ftp_host.stat_cache), "entries in cache"
    ftp_host.close()


if __name__ == '__main__':
    main()


# Time without caching:
# real    18m10.675s
# user    0m2.660s
# sys     0m0.796s

# Time without cache, with current directory cache
# real    13m32.333s
# user    0m2.404s
# sys     0m0.672s

# Second day
# real    14m36.256s
# user    0m2.080s
# sys     0m0.672s

# real    13m55.254s
# user    0m2.868s
# sys     0m0.824s
           
# Time with "infinite" cache, with current directory cache
# real    1m30.117s
# user    0m0.480s
# sys     0m0.112s

# Ditto, together with caching in listdir
# real    0m49.677s
# user    0m0.424s
# sys     0m0.100s

# Ditto, with LRU cache of 5000 elements instead of "infinite" dictionary
# real    1m1.007s
# user    0m12.641s
# sys     0m0.160s

