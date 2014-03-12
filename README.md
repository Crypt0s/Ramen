Ramen2 (Alpha)
======
Ramen2 is a Python framework that allows users to utilize community-written network protocol handlers written for the Ramen Project.
The network protocol handlers allow network protocols and network filesystems to be accessed through a POSIX-like standard filesystem interface.  The project then runs those handlers against a target(s), stores metadata it collects, and runs user/community plugins based on collected attributes.

An example usage of this project would be scanning a netblock for WebDAV, collecting timestamps, author name, file permissions, and path data while opening and running a MD5sum operation over every file with the extension .pst created between the dates of January and March.

Results are stored in an object database for running queries and reports.

Features
========
* Plugins for each Filesystem
* Well-defined interface for writing your own protocol/filesystem handlers
* Automated discovery and enumeration of targets
* Support for user plugins to do things like search for keywords, get file hashes, run SSDEEP, ect...

Plugins
=======
* MD5hash

Filesystem Support
==================
* Local Disk
* Sharepoint WebDav
* WebDav

In-Progress
===========
* Web application user interface

Install Procedures
==================
* To be filled when project stabilizes

Known Issues
============
* To be filled when project stabilizes
