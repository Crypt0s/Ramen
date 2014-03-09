#!/usr/bin/python
import pdb,os
import imp

# If you need additional settings/setup/passwords/whatever, you set them in a companion settings file found in the fs_settings folder.
# If one wanted to use the settings from the settings file for Ramen itself, one would specify that file instead of one in fs_settings.
settings = imp.load_source('settings','fs_settings/local_disk.py')
#pdb.set_trace()
# this should match the human-readable name to be used in the targets.txt file.
product = 'local_disk'
class filesystem:

    def __init__(self,*args):
        pass

    def stat(self,path):
        stat = os.stat(path) # code for returning a tuple like os.stat()
        return stat

    def open(self,path):
        #new_fd = fd(path)
        #return new_fd
        return open(path,'r')

    def validate(self,target):
        return True

    def walk(self,path):
        return os.walk(path)
