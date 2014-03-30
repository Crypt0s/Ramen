Ramen2 (Alpha)
======
Ramen2 is a Python framework that allows users to utilize community-written network protocol handlers written for the Ramen Project.
The network protocol handlers allow network protocols and network filesystems to be accessed through a POSIX-like standard filesystem interface.  The project then runs those handlers against a target(s), stores metadata it collects, and runs user/community plugins based on collected attributes.

An example usage of this project would be scanning a netblock for WebDAV, collecting timestamps, author name, file permissions, and path data while opening and running a MD5sum operation over every file with the extension .pst created between the dates of January and March.

Results are stored in an object database for running queries and reports in ways that don't require a lot of code and that will be intuitive to even novice programmers.


Features
========
* Modules for each Filesystem
* Support for user plugins to do things like search for keywords, get file hashes, run SSDEEP, ect...
* Well-defined interface for writing your own protocol/filesystem handlers
* Automated discovery and enumeration of targets

Plugins
=======
* MD5hash

Filesystems Supported
==================
* Local Disk
* FTP
* HTTP

Filesystems In-Progress
=======================
* Sharepoint WebDav
* WebDav

Install Requirements
==================
* Python 2.7
* ZODB & its prerequisites
* Beautifulsoup (for the HTTP handler)

Known Issues
============
* The user interface is junky

To-Do:
======
1. Stabilize the configuration of the Object Database
2. Plan and build User Interface to automate + configure Ramen
3. Incorporate Additional Filesystems and Plugins (ssdeep, webDAV, sharepoint, ect...)
4. Integrate with Maltego
