import settings,socket,os,struct
from subprocess import call
import pdb

def ip_expand(target):
    network = target.split('/')[0]
    hosts = target.split('/')[1]
    result = []
    for i in xrange((2**(32-int(hosts)))):
        result.append(socket.inet_ntoa(struct.pack('!I',struct.unpack('!I', socket.inet_aton(network))[0]+i)))
    return result

def mount(server,share):
    path = 'smb://'+server+'/'+share+'/'
    mountpoint = settings.MOUNT_LOCATION+server+'/'+share
    print ' '.join(["mount","-t","cifs","//"+server+'/'+share,mountpoint,"-o","ro,username="+settings.USERNAME+",password="+settings.PASSWORD])
    try:
        os.makedirs(mountpoint)
        #TODO: Security issue with funky-named shares with shell chars in them?
        call(["mount","-t","cifs","//"+server+'/'+share,mountpoint,"-o","ro,username="+settings.USERNAME+",password="+settings.PASSWORD])
    except OSError:
        print "Folder couldn't be created"
    except:
        print "Mount error"
    return mountpoint

def umount(location):
    try:
        call(["umount",location])
        # I make a directory there to hold it so that must be deleted too.
        os.rmdir(location)
    except:
        print "Failed to unmount " + location + " when asked."
        return False
    return True

def loadmodules(folder):
    dirs = os.listdir(folder)
    # recursive load any subdirectories
    subdirs = []
    function_array = []
    # Make sure the init.py is there, marking that the folder is a module
    if '__init__.py' not in dirs:
        return None
    # Load sub-modules in * fashion
    for item in dirs:
        if os.path.isdir(os.path.abspath(folder+'/'+item)):
            dirs.remove(item)
            function_array += loadmodules(folder+'/'+item)
        else:
            # Don't try to import pyc or init files.
            split = item.split('.')
            name = split[0]
            extension = split[-1]
            # Todo: load pyc files so we don't have to recompile!
            if extension == 'pyc' or name == '__init__' or name == None:
                pass
            elif extension == 'py':
                folder = folder.replace(os.sep,'.')
                mod = __import__(folder+'.'+name)
                for sub in folder.split('.')[1:]:
                    mod = getattr(mod,sub)
                funct = getattr(mod,name)
                function_array.append(funct)
    # Return an array of loaded module objects
    return function_array
