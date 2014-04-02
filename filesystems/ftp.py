#!/usr/bin/python
import imp
from BTrees import OOBTree
import persistent
import ftplib
import ftputil
import pdb
# If you need additional settings/setup/passwords/whatever, you set them in a companion settings file found in the fs_settings folder.
# If one wanted to use the settings from the settings file for Ramen itself, one would specify that file instead of one in fs_settings.
settings = imp.load_source('settings','fs_settings/ftp.py')

# this should match the human-readable name to be used in the targets.txt file.
product = 'ftp'
class filesystem(persistent.Persistent):

    def __init__(self,host):
        self.host = ftputil.FTPHost(host,settings.username,settings.password,session_factory=ftplib.FTP)
        self.product = "ftp"
        # required
        self.root = OOBTree.OOBTree()

    def stat(self,path):
        print '.',
        try:
            mstat = self.host.stat(path) # code for returning a tuple like os.stat()
            return mstat
        except:
            import traceback
            print traceback.format_exc()
            return (None,None,None,None,None,None,None,None,None,None)

    def is_dir(self,path):
        return self.host.path.isdir(path)

    def open(self,path):
        # Already returns a FP equivalent.  Neat.
        return self.host.open(path,'r')

    def validate(self,target):
        try:
            # Attempt to connect to the Host and successfully perform a directory listing.
            host = ftputil.FTPHost(target.host,settings.username,settings.password,session_factory=ftplib.FTP)        
            host.listdir('/')
            host.close()
            return True
        except:
            import traceback
            print traceback.format_exc()
            return False

    def walk(self,path):
        return self.host.walk(path)

    #lets us access the storage
    @property
    def w_root(self):
        # assume that if we are accessing the file tree in this manner that we must be intending to change it.
        self._p_changed = 1
        # Python returns refs (with the exception of several notable cases) so this should be fine.
        return self.root


# unit-testish thing here.
if __name__ == "__main__":
    pass
