#!/usr/bin/python
#
# This is an example action plugin
# Action plugins run on *every* file no matter what.
#
# If you want selective matching based on a file attribute, you should write an
# extension plugin

from hashlib import md5

# All action plugins have an action method that gets called by the scanner process
# The scanner process doesn't do anything with the action returned values, it's up to you to store it in the DB or perform some action
def action(attr):
    blocksize = 65536
    md5hash = md5()
    with open(attr.path,'r') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            md5hash.update(buf)
            buf = afile.read(blocksize)
    hash = md5hash.digest()
    print hash.encode('hex')
    # Here is where you'd interface with the DB to *SAVE IT YOURSELF*
    # Note that you'll need to run django syncdb for the DB results to show up
    # ...and you'll need to add code to the django search view.
    return hash.encode('hex')

# This is for testing purposes
if __name__ == "__main__":
    import sys,os
    # Quick hack as this needs to pull in the class "fileattr" from utils
    sys.path.append('../../')
    import utils
    attr = utils.fileattr(os.path.abspath(sys.argv[1]),os.stat(sys.argv[1]),None)
    result = action(attr)
    print result
