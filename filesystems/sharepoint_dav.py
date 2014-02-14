#!/usr/bin/python
import python_webdav.connection as webdav_connection
import python_webdav.client as webdav_client
import requests
import pdb
## TODO: Remove
#debug = True
#if debug == True:
#    import imp
#    settings = imp.load_source('settings','/root/Projects/Ramen/settings.py')
## End

settings = imp.load_source('settings','../fs_settings/sharepoint_dav.py')

product = 'sharepoint'

# we could verify that this is a sharepoint webdav by doing a OPTIONS request and looking for the webdav version I think.

class Filesystem:

    def __init__(self,host,share_folder,username,password,port):
        # placeholder -- this is stuff you would need if you were using authenticated HTTP as your FS
        settings_dict = {'username':settings.USERNAME,'password':settings.PASSWORD,'domain':settings.DOMAIN,'host':host,'path':share_folder,'auth':'NTLM','allow_bad_cert':True,'realm':'','port':port}
        self.connection = webdav_connection.Connection(settings_dict)


    # This routine validates that the target has a running instance of the service.
    @staticmethod
    def validate(targetobj):
        for port in targetobj.ports:
            try:
                # todo: use format printing to get better speed.
                headers = requests.get(targetobj.host+':'+port,verify=False).headers.keys()
                if 'microsoftsharepointteamservices' in headers:
                    return True
            except:
                # Looks like host is unreachable...
                return False
        # we went thru the open ports and came up empty
        return False

    def stat(self,path):
        # zero is the depth
        file = self.connection.get_properties(path,0)[0]
        #posix.stat_result(st_mode=16749, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime=1387226717, st_mtime=1382991091, st_ctime=1382991091)
        # Todo - Merge win32 time and the sharepoint DAV times, keeping youngest times.
        if file == [] or file == None:
            print "no file found"
            raise IOError
        # Todo: last accessed time?
        stat = (file.attrs, None, None, None, None, None, file.size, None, file.mtime, file.ctime)
        return stat

    # TODO: This isn't right -- we need to split out the owner info and stuff -- perhaps we need a unified file object as well to hold and retrieve data values
    # Sharepoint doesn't store acl's per-se, but it has this
    def getfacl(self,path):
        #return self.connection.get_properties(path,depth).attrs
        # Returns a list of lists right now
        # Todo: Have some sort of actual permission object that can be serialized to db?

        # Right now this only ever returns the last person to modify the file -- need to look to see if i can use sharepoint DAV to get more info on the windows perms
        return [[self.connection.get_properties(path,0).modifiedby,'RW']]

    def _walker(self,path):
        folders = []
        files = []
        res = self.connection.get_properties(path,1)
        for file in res:
            if file.folder is True:
                folders.append(file)
            elif file.folder is not True:
                files.append(file)
        return (path,folders,files)

    # Wraps _walker in a generator for os.walk-like interfacing.
    def walk(self,path):
        folders = self._walker(path)[1]
        for folder in folders:
            res = self._walker(path+'/'+folder.name)
            yield res

    def open(self,path):
        new_fd = fd(path)
        return new_fd

#File descriptor class for reasons
class fd:
    # if you need to do something like send an HTTP request, or have username/password/GET parameters, you want to make the request happen here, and change the init parameters to what you want to have in the request.
    def __init__(self,connection,path):
        self.connection = connection
        self.read_bytes = 0
        self.read_lines = 0
        self.path = path
        self.EOF = False
        # NOTE: Path may need to be set to a relative url and then have the send_get method add it to the url
        self.data = self.connection.send_get(path)[1] #[1] is the location of the content in the returned tuple

    # Most of your code is probably going in to this bit if too
    def read(self,bytes):
        #whatever code you need for getting the "file" and giving out X bytes goes here
        #self.data = "" # data should be set in the __init__ maybe?
        info = self.data[self.read_bytes:self.read_bytes+bytes]
        self.read_bytes += bytes
        if info == '':
            self.EOF = True
        return info

    # Just in case.
    def seek(bytes):
        if bytes < 0:
            self.EOF = False
        # Don't know if this needs to be implemented or not but...
        #if bytes > self.size:
        #    self.EOF = True
        read_bytes+=bytes
        return True

    def readlines(self):
        linereader = read_gen()
        lines = []
        # The try catches the generator crash and passes the object off.
        try:
            while linereader:
                lines.append(linereader.next())
        except:
            return lines

    def readline(self):
        if self.linereader == None:
            self.linereader = read_gen()
        else:
            # This should raise an EOF
            try:
                return linereader.next()
            except:
                return None;

    def read_gen(self):
        self.read_lines += 1 
        array = []
        while self.EOF == False:
            byte = self.read(1)
            if byte == "\n" or self.EOF == True:
                array.append(byte)
                line = array
                array = []
                yield ''.join(line)
            else:
                array.append(byte)
        yield None

    def close(self):
        del self

if __name__ == "__main__":
    # UNIT TEST 1
    settings_debug = {'port':'','host':'','path':'','realm':'','domain':'asrcfh','auth':'NTLM','allow_bad_cert':True,'username':'','password':''}
    conn = webdav_connection.Connection(settings_debug)
    #host,share_folder,username,password
    # UNIT TEST 2
    share_conn = sharepoint_dav_filesystem(settings_debug['host'],settings_debug['path'],settings_debug['username'],settings_debug['password'],settings_debug['port'])
    # UNIT TEST 3    
    results = share_conn.stat('')
    url = ''

    print results
    res = share_conn.connection.get_properties(url, 1)
    res = share_conn.walker(url)
