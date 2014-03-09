#!/usr/bin/python
import pdb
import imp

# If you need additional settings/setup/passwords/whatever, you set them in a companion settings file found in the fs_settings folder.
# If one wanted to use the settings from the settings file for Ramen itself, one would specify that file instead of one in fs_settings.

# this should match the human-readable name to be used in the targets.txt file.
product = 'test'

settings = imp.load_source('settings','fs_settings/fs.py')



class filesystem:

    def __init__(self,ip,uri,username,password):
        # placeholder -- this is stuff you would need if you were using authenticated HTTP as your FS
        self.ip = ip
        self.uri = uri
        # this is where you'd establish the object that actually allows interface to the file (this file abstracts all the specific methods of that access with these methods known to Ramen)
        self.fs_object = (username,password)

    def stat(self,path):
        stat = None # code for returning a tuple like os.stat()
        return stat

    def open(self,path):
        new_fd = fd(path)
        return new_fd

    def validate(self,target):
        # Code that verifies that the target is running a filesystem which this handler can handle goes here.
        # In a nutshell - portscan for open ports, get the header, compare it to what this handles, and then say if the target is able to be interfaced with using this handler.

        return True

#File descriptor class for reasons
class fd:
    # if you need to do something like send an HTTP request, or have username/password/GET parameters, you want to make the request happen here, and change the init parameters to what you want to have in the request.
    def __init__(self,path):
        self.read_bytes = 0
        self.read_lines = 0
        self.path = path
        self.EOF = False
        # A fair amount (if not all) of your code will go into setting the data variable
        # if data is large, i reccomend that you set it as a generator or something?
        self.data = "Something happened and set the value of this string\nthis is the next line\n we have another line after this one\nthis is the last line."


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

    
