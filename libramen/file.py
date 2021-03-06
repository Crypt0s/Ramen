#!/usr/bin/python

##########################
#        File.py         #
#The filesystem class(tm)#
##########################
import time
import persistent

class File(persistent.Persistent):
    def __init__(self, filename, relpath, stat, target, folder=False):

        # simplest - just takes the time right now
        self.scan_date = int(time.time())
        self.filename = filename

        # stores obj ref to the parent folder of this file
        self.relpath = relpath
        #self.perms = perms
        self.target = target

        # split out the stat junk later
        self.stat = stat

        # bool that sets if this is a folder or not.
        self.folder = folder

        # store the object in the ZODB automatically
        

    def tostring(self):
        #todo: Make this happen
        return self.stat
