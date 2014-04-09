ftputil
=======

Purpose
-------

ftputil is a high-level FTP client library for the Python programming
language. ftputil implements a virtual file system for accessing FTP
servers, that is, it can generate file-like objects for remote files.
The library supports many functions similar to those in the os,
os.path and shutil modules. ftputil has convenience functions for
conditional uploads and downloads, and handles FTP clients and servers
in different timezones.

What's new?
-----------

Note: This version of ftputil is _not_ backward-compatible
with earlier versions. See the links below for information
on adapting existing client code.

Since version 2.8 the following changed:

- This version adds Python 3 compatibility! :-)

  The same source is used for Python 2.x and Python 3.x.

  I had to change the API to find a good compromise for
  both Python versions. This means this version is _not_
  backward-compatible with earlier ftputil versions.

- ftputil now requires at least Python 2.6.

- Remote file-like objects use the same semantics as Python's
  `io` module. (This is the same as for the built-in `open`
  function in Python 3.)

- `ftputil.ftp_error` was renamed to `ftputil.error`.

- For custom parsers, import `ftputil.parser` instead of
  `ftputil.stat`.

For more information please read
http://ftputil.sschwarzer.net/trac/wiki/Documentation
http://ftputil.sschwarzer.net/trac/wiki/WhatsNewInFtputil3.0

Documentation
-------------

The documentation for ftputil can be found in the file ftputil.txt
(reStructuredText format) or ftputil.html (recommended, generated from
ftputil.txt).

Prerequisites
-------------

To use ftputil, you need Python, at least version 2.6. Python is a
programming language, available from http://www.python.org for free.

Installation
------------

- *If you have an older version of ftputil installed, delete it or
  move it somewhere else, so that it doesn't conflict with the new
  version!*

- Unpack the archive file containing the distribution files. If you
  had an ftputil version 2.8, you would type at the shell prompt:

    tar xzf ftputil-2.8.tar.gz

  However, if you read this, you probably unpacked the archive
  already. ;-)

- Make the directory to where the files were unpacked your current
  directory. Assume that after unpacking, you have a directory
  `ftputil-2.8`. Make it the current directory with

    cd ftputil-2.8

- Type

    python setup.py install

  at the shell prompt. On Unix/Linux, you have to be root to perform
  the installation. Likewise, you have to be logged in as
  administrator if you install on Windows.

  If you want to customize the installation paths, please read
  http://docs.python.org/inst/inst.html .

If you have pip or easy_install installed, you can install the current
version of ftputil directly from the Python Package Index (PyPI)
without downloading the package explicitly.

- Just type

    pip install ftputil

  or

    easy_install ftputil

  on the command line, respectively. You'll probably need
  root/administrator privileges to do that (see above).

License
-------

ftputil is Open Source Software. It is distributed under the
new/modified/revised BSD license (see
http://opensource.org/licenses/BSD-3-Clause ).

Authors
-------

Stefan Schwarzer <sschwarzer@sschwarzer.net>

Evan Prodromou <evan@bad.dynu.ca> (lrucache module)

Please provide feedback! It's certainly appreciated. :-)


[1] http://ftputil.sschwarzer.net/trac/ticket/65
[2] http://lists.sschwarzer.net/pipermail/ftputil/2012q3/000350.html
[3] http://ftputil.sschwarzer.net/trac/ticket/39
    http://ftputil.sschwarzer.net/trac/ticket/65
    http://ftputil.sschwarzer.net/trac/ticket/66
    http://ftputil.sschwarzer.net/trac/ticket/67
    http://ftputil.sschwarzer.net/trac/ticket/69
[4] http://lists.sschwarzer.net/listinfo/ftputil
[5] http://lists.sschwarzer.net/listinfo/ftputil-tickets
