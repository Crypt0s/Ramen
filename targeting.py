#!/usr/bin/python
#
#
#           Targeting.py
#
#       A Part of Project Ramen
#
#   
#
#   Targeting.py is the targeting subsystem for Ramen.  Basically, it determines which file system to use based on user input or autodetection
#   This code parses both the user input in the targeting file and selects the correct filesystem with which to scan the target
#
import pdb
import utils
import settings
import persistent

class targeter:
    # Info can be anything additional information that the target has that needs to be passed into it's filesystem handler in order to function properly.
    # A good example would be the folder for WebDAV or a URL for a website.
    def __init__(self):
        #self.scanner = nmap.PortScanner()
    
        # Load a list of filesystem names (from NMAP) and their handlers into a dictionary
        self.scannables = {}
        filesystems = utils.loadmodules('filesystems')
        for a_filesystem in filesystems:
            self.scannables[a_filesystem.product] = a_filesystem

    def parse(self):
        # Parse expects the format to be ip[tab]fsname
        target_list = settings.TARGET_LIST
        with open(target_list,'r') as target_file:
            targets = target_file.readlines()
            targets = [x.strip() for x in targets]
        # return target objects with properly associated filesystem types
        target_objects = []
        for atarget in targets:
            split_atarget = atarget.split()
            ip = split_atarget[0]

            # TODO: Feels like this section could be written better since i repeat myself a lot.
            # if there is no specified fs, try them all
            if len(split_atarget) == 1:
                for fs in self.get_filesystem_handler():
                    my_fs = self.get_filesystem_handler(fs)
                    fsobj = my_fs
                    target_objects.append(target(ip,fsobj))

            # if there are multiple spec'd
            elif ',' in split_atarget[1]:
                for fs in split_atarget[1].split(','):
                    my_fs = self.get_filesystem_handler(fs)
                    fsobj = my_fs[0]
                    fsinfo = my_fs[1]
                    target_objects.append(target(ip,fsobj))

            # if there is only one spec'd
            else:
                try:
                    fs = self.get_filesystem_handler(split_atarget[1])
                    fsobj = fs
                except:
                    print "Didn't understand directive for " + ip + " please examine the config file for errors"

                target_objects.append(target(ip,fsobj))

        return target_objects
        
    # Targeting subsystem will ensure that each target object has a filesystem with it.
    def get_filesystem_handler(self,fsname=None):
        # overridden for convenience.  not for looks.
        if fsname == None:
            return self.scannables.keys()
        if fsname.lower() in self.scannables.keys():
            filesystem = self.scannables[fsname.lower()]
        # now see if there is any extra information in the settings department...
        # return the filesystem module and info
        return filesystem
    # This validates just the current target object -- we need a fast method to quickly validate hundreds of thousands of targets.


# The filesystem attribute is used outside of the database -- we create target,filesystem pairs to feed to the scanner but we store the targets in the database with multiple filesystems, hence "filesystems" attr.
    
class target(persistent.Persistent):
    # host - the url, ip, or host name of the target
    # service - the name of the service that is being targeted (smb, nfs, ftp, http, ect...)
    # Filesystem - Filesystem module object.
    def __init__(self, host, filesystem):
        self.host = host
        self.ports = [] # TODO: use ports
        # The filesystem settings and such are set in the settings file -- it's easier that way for now until we have a structured settings python import thing
        self.filesystem = filesystem.filesystem(host)
        self.filesystems = {}

    def validate(self):
        # send itself to the filesystem handler validation subroutine for validation
        # return the result to the requester (probably main()) so that the target can be deleted from the list.
        return self.filesystem.validate(self)

    def tostring(self):
        return self.host+' - '+str(self.filesystem)
