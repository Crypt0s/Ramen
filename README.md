Ramen
======
Ramen is a Python Project that aims to discover all the files on your network.  Specifically, Ramen supports CIFS/SMB file share discovery, enumeration, and attribute storage and retrieval.

In the future, Ramen will support as many file types as there are network file systems.

Features
=======
* Storage of file attributes (user permissions, filename, path right now, more to come)
* Automated discovery and enumeration across netblocks
* A User Interface with which to retrieve stored file/file information
* Multi-threaded _fast_ operation

In-Progress
===========
1. File-type actions
2. File Timestamp storage
3. User plugins
4. Additional Network File System Support
5. Anonymous access

Install Procedures
===================
Requirements:
------------
```
build-essential
python-devel
samba-winbind-devel
automake
```

Steps:
-----
1) install:
```
	libsmbclient
	libsmbclient-devel
	psycopg2
	postgresql
	postgresql-server
	Django (1.5 or above)
	Python (2.6 or 2.7, not tested w/>3,0)
	Python-devel
	pysmbc - https://pypi.python.org/packages/source/p/pysmbc/pysmbc-1.0.13.tar.bz2
```
2) go to cifsacl:
```
	autoreconf -i
	./configure
	make
	make install
	python setup.py build
	python setup.py install
```
3) go to pysmbc-1.0.13:
```
	make
	python setup.py build
	python setup.py install
```
4) Configure your settings in settings.py

5) Create the database -- If you're new to postgres, this part will slow you down a little, but it's really easy w/Google.
```
	service postgresql start
	su postgres
	createdb -p 5432 smb_scan
```
6) start the Django application
```
	change your postgres server settings:
		nano web_interface/smb_scan/smb_scan/settings.py
	cd web_interface/smb_scan
	python manager syncdb
	python manager.py runserver 0.0.0.0:8080
```
7) be sure to clear your firewall/disable selinux
```
	iptables --flush
```
8) fill out targets.txt with targets

9) start the scanner
```
	python beta.py
```
10) browse to http://[yourcomputerip]:8080/scanner/

