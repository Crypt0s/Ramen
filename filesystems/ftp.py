#!/usr/bin/python
import imp
from BTrees import OOBTree
import persistent
import ftplib
import ftputil

# If you need additional settings/setup/passwords/whatever, you set them in a companion settings file found in the fs_settings folder.
# If one wanted to use the settings from the settings file for Ramen itself, one would specify that file instead of one in fs_settings.
settings = imp.load_source('settings','fs_settings/ftp.py')

# this should match the human-readable name to be used in the targets.txt file.
product = 'ftp'
class filesystem(persistent.Persistent):

    def __init__(self,*args):
        self.host = ftputil.FTPHost(site,settings.username,settings.password,session_factory=ftplib.FTP)
        self.product = "ftp"
        # required
        self.root = OOBTree.OOBTree()
        pass

    def stat(self,path):
        try:
            stat = self.host.stat(path) # code for returning a tuple like os.stat()
            return stat
        except:
            return None

    def is_dir(self,path):
        return host.path.isdir(path)

    def open(self,path):
        # Already returns a FP equivalent.  Neat.
        return host.open(path,'r')

    def validate(self,target):
        try:
            # Attempt to connect to the Host and successfully perform a directory listing.
            self.host = ftputil.FTPHost(site,settings.username,settings.password,session_factory=ftplib.FTP)        
            host.listdir('/')
            host.close()
            return True
        except:
            return False

    def walk(self,path):
        return host.walk(path)

    #lets us access the storage
    @property
    def w_root(self):
        # assume that if we are accessing the file tree in this manner that we must be intending to change it.
        self._p_changed = 1
        # Python returns refs (with the exception of several notable cases) so this should be fine.
        return self.root
