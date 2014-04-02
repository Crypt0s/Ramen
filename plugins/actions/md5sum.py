#!/usr/bin/python
#
# This is an example action plugin
# Action plugins run on *every* file no matter what.
#
# If you want selective matching based on a file attribute, you should write an
# extension plugin

from hashlib import md5
import re
import pdb
# All action plugins have an action method that gets called by the scanner process
# The scanner process doesn't do anything with the action returned values, it's up to you to store it in the DB or perform some action
def action(fileobj,filesystem):
  try:
    if fileobj.folder == True:
        return None

    # This is too...unlikely to be correct.
    # Regular files only, thx.  (this may also get socket files...)
    #if (fileobj.stat.st_mode < 10000):
    #    return None

    if re.search('^(/dev|/proc|/sys)',fileobj.relpath) is not None:# or fileobj.target.filesystem.is_dir(fileobj.relpath) is True:
        print 'none'
        return None

    file_desc = filesystem.open(fileobj.relpath+'/'+fileobj.filename)
    blocksize = 65536
    md5hash = md5()
    buf = file_desc.read(blocksize)
    while len(buf) > 0:
        md5hash.update(buf)
        buf = file_desc.read(blocksize)
    hash = md5hash.digest()
    #print hash.encode('hex')

    fileobj.hash = hash
    return hash.encode('hex')
  except:
    # This happens when it's a folder, usually.
    #import traceback
    #print traceback.format_exc()
    #print fileobj.relpath+'/'+fileobj.filename
    #pdb.set_trace()
    return None

# This is for testing purposes
if __name__ == "__main__":
    import sys,os
    # Quick hack as this needs to pull in the class "fileattr" from utils
    sys.path.append('../../')
    import utils
    attr = utils.fileattr(os.path.abspath(sys.argv[1]),os.stat(sys.argv[1]),None)
    result = action(attr)
    print result
