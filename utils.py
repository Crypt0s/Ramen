import ldap,settings,socket,smbc,os,struct
from cifsacl import *
from subprocess import call

def list_shares(server):
    found_shares = {}
    ctx = smbc.Context()
    if settings.ANONYMOUS == True:
        ctx.optionNoAutoAnonymousLogin = False
    else:
        ctx.optionNoAutoAnonymousLogin = True
        # You want to do it this way otherwise things get out of order???
        cb = lambda se, sh, w, u, p: (settings.DOMAIN, settings.USERNAME, settings.PASSWORD)
        ctx.functionAuthData = cb
        server = server.strip()
        try:
            entries = ctx.opendir('smb://'+server).getdents()
            progress = 0
            for entry in entries:
                try:
                    progress+=1
                    #print "Progress: " + str(progress/len(entries)*100)
                    # 3L type is a share
                    if entry.smbc_type == 3L and "$" not in entry.name:
                         print entry.name
                         share = entry.name
                         if server in found_shares.keys():
                            found_shares[server].append(share)
                         else:
                             found_shares[server]=[share]
                except:
                    print "Error connecting to " + server
                    pass
        except smbc.PermissionError:
            print "Permission denied"
            pass
        except smbc.TimedOutError:
            print "Server " + server + " Timed Out."
            pass

    return found_shares


def bind_domain():
    ad = ldap.initialize('ldap://'+settings.DOMAIN_CONTROLLER)
    ad.set_option(ldap.OPT_REFERRALS, 0)
    ad.simple_bind_s(settings.LDAP_USERNAME,settings.LDAP_PASSWORD)
    return ad

def resolve(ad,acl_entry):
    # One of the hardest-fought bugs lived here -- only use synchronus functions in the LDAP package...buggy.
    permlist = []
    # The _s means syncronus -- use only them as the async has bugs!
    base = settings.SEARCH_BASE
    scope = ldap.SCOPE_SUBTREE
    attrs = ['cn']
    for entry in acl_entry:
        if '::' in entry:
            entry_split = entry.split('::')
            sid = entry_split[0]
            acl_col_1 = entry_split[1]
            # Todo: this is a dirty hack -- why do we have weird SIDs like this???
            try:
                acl_col_2 = entry_split[2]
            except:
                #print "Weird SID Warning: " + entry
                acl_col_2 = '?'                    
        else:
            sid = entry
            acl_col_1 = "?"
            acl_col_2 = "?"

        test = "objectsid=%s" % sid
        #ad.simple_bind(username,password)
        result = ad.search_s(base,scope,test,attrs)
        try:
            permlist.append([result[0][1][attrs[0]][0],acl_col_1,acl_col_2])
        except:
            pass
    return permlist

# Borrowed the below function from noodle-ng https://code.google.com/p/noodle-ng/  
def checkSMB(ip):
    """ looks for running samba server """
    # check if the server is running a smb server
    sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # This may need to get changed on high-latency links...
    sd.settimeout(1)
    try:
        sd.connect((ip, 445))
        sd.close()
        return ip
    except:
	pass

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
            if extension == 'pyc' or name == '__init__':
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

class fileattr:
    def __init__(self,fullpath,attr,perms):
        self.perms = perms
        self.ctime = attr.st_ctime
        self.atime = attr.st_atime
        self.mtime = attr.st_mtime
        self.size = attr.st_size
        self.path = fullpath
        self.filename = fullpath.split('/')[-1:][0]
