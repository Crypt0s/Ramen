#! /usr/bin/env python

import ftplib
import ftputil


ftp_host = ftputil.FTPHost("localhost", "ftptest",
                           "d605581757de5eb56d568a4419f4126e")
ftp_host._session.set_debuglevel(2)
#import pdb; pdb.set_trace()
ftp_host.listdir("/rootdir2")

print

ftp = ftplib.FTP("localhost", "ftptest", "d605581757de5eb56d568a4419f4126e")
ftp.set_debuglevel(2)
ftp.cwd("/")
ftp.cwd("/")
ftp.dir("-a")
