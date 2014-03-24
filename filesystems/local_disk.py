#!/usr/bin/python
import pdb,os
import imp
from BTrees import OOBTree
import persistent

# If you need additional settings/setup/passwords/whatever, you set them in a companion settings file found in the fs_settings folder.
# If one wanted to use the settings from the settings file for Ramen itself, one would specify that file instead of one in fs_settings.
settings = imp.load_source('settings','fs_settings/local_disk.py')
#pdb.set_trace()
# this should match the human-readable name to be used in the targets.txt file.
product = 'local_disk'
class filesystem(persistent.Persistent):

    def __init__(self,*args):
        self.product = "local_disk"
        # required
        self.root = OOBTree.OOBTree()
        pass

    def stat(self,path):
        try:
            stat = os.stat(path) # code for returning a tuple like os.stat()
            return stat
        except:
            return None

    def is_dir(self,path):
        return os.path.isdir(path)

    def open(self,path):
        #new_fd = fd(path)
        #return new_fd
        return open(path,'r')

    def validate(self,target):
        return True

    def walk(self,path):
        return os.walk(path)

    #lets us access the storage
    @property
    def w_root(self):
        # assume that if we are accessing the file tree in this manner that we must be intending to change it.
        self._p_changed = 1
        # Python returns refs (with the exception of several notable cases) so this should be fine.
        return self.root
