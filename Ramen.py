#!/usr/bin/python

###########################
#      ~~ Ramen2 ~~
#
#   Ramen2 is designed to allow users (security researchers, network managers, system administrators) to quickly index network and local filesystems and collect metadata about the files.
#   Ramen provides a convenient interface that allows users to write POSIX-like Filesystem handlers around network protocols and stores the results in an object database for retrieval and storage.
#
###########################

# For queue (most of these are now legacy from the first implementation)
import multiprocessing, threading, os, settings, logging, random
from multiprocessing import Pool, Queue
from multiprocessing.pool import ThreadPool

# For DB
import ZODB, ZODB.FileStorage
import transaction
import copy

# for debug
import pdb

#for saving
import signal
import pickle
import sys

# imports all custom modules in the libramen folder.
from libramen import *

#from file import File
File = file.File

queue = None

def thread_manager(target_queue):
    # Handles the queue process in a way that is more resiliant to errors than mapped pools, which can fail on python segfaults.
    global queue
    queue = multiprocessing.Queue()
    [queue.put(target) for target in target_queue]
    processes = []

    for i in xrange(settings.MAX_THREADS):
        p = multiprocessing.Process(target=scanprocess,args=([queue]))
        processes.append(p)

    for p in processes:
        p.start()

    while queue.qsize()>0 and len(processes) > 0:
        for p in processes:
            if p.exitcode is not None and queue.qsize()>0:
                print "Restarting dead thread -- " + str(queue.qsize()) + " More jobs left"
                p.join(3)
                processes.remove(p)
                del p
                p = multiprocessing.Process(target=scanprocess,args=([queue]))
                p.start()
                processes.append(p)
            if len(processes) < settings.MAX_THREADS and queue.qsize()>0:
                print "Thread-starved conditions detected, starting additional threads"
                for i in range(settings.MAX_THREADS-len(processes)):
                    print "Started"
                    p = multiprocessing.Process(target=scanprocess,args=([queue]))
                    p.start()
                    processes.append(p)
            if p.exitcode == 0 and queue.qsize() == 0:
                processes.remove(p)
                del p
                print "Joined thread"

    if queue.qsize()==0:
        return
    else:
        print "Thought i didn't have anything to do but i was wrong, re-starting"
        thread_manager([queue.get() for i in range(queue.qsize())])

def runmodules(fileobj,filesystem):
    # Don't Repeat Yourself - holds the code for running a file object through the user-provided plugins.
    # Actions
    for module in actions:
        try:
            fileobj = module.action(fileobj,filesystem)
        except:
            print "Action failed"
            import traceback
            print traceback.format_exc()

    # Extensions    
    for module in extensions:
        try:
            if module.__match__(fileobj):
                fileobj = module.action(fileobj,filesystem)
        except:
            print "Extension Failed."
            import traceback
            print traceback.format_exc()
    return fileobj

def scanprocess(queue,debug=None):

    if debug is None:
        # Cute little naming trick for debug only.
        name = random.randint(0,1000)
        while queue.qsize()>0:
            print str(name)+": looking for work"
            try:
                # the target is a tuple (targetobject,folder)
                target = queue.get(True,5)
                # targetobj = target[0]
                # folder = target[1]
            except:
                print "No work."
                exit(0)
            print str(name) +": Got some work : "
    else:
        target = debug

    print target.tostring()

    # We should always start with the root - /
    # Note: So one of the weird things that this framework is going to require the plugin-writers to handle is stuff like drive letters in windows.
    # Ideally, you'd take this slash in your filesystem handler, know that it's seeking the "My Computer" and return a list of the connected drives
    # Then, youd let it go to each drive recording the drive letter as another folder in the chain.  That's how i'd do it, anyways.
    walker = target.filesystem.walk('/') 
    
    #determine if this target/fs combo exists already
    if db.has_key(target.host):
        if db[target.host].filesystems.has_key(target.filesystem.product):
            # we already have the object scanned -- get the writeable root and start writing on top of it.
            pass
        else:
            # we have the target, but not the fs
            db[target.host].filesystems[target.filesystem.product] = target.filesystem
    else:
        target.filesystems = {target.filesystem.product:target.filesystem}
        db[target.host] = target
    store = db[target.host].filesystems[target.filesystem.product].w_root

    # SO, store now refrences the target and filesystem combo that we have in the db
    while 1:
        try:
            # grab the next batch of files from the next folder
            fullpath,folders,files = walker.next()
            print 'walked'
        
            # parse and get the rel obj
            relpath = fullpath.split('/')
            # make sure that if the path was root (/) that we set it because the split strips single-slashes at the beginning.
            if relpath[0] == "":
                relpath[0] = '/'

            print fullpath
            #posix.stat_result(st_mode=33188, st_ino=2621703, st_dev=2050L, st_nlink=1, st_uid=0, st_gid=0, st_size=30, st_atime=1395927104, st_mtime=1175771922, st_ctime=1393946695)
            # File signature: class File(filename, relpath, stat, target, folder=False):
            # stat the folder and save it
            folderstat = target.filesystem.stat(fullpath)
            folderobj = File(relpath[-1],fullpath,folderstat,target,True)
            folderobj = runmodules(folderobj,target.filesystem)
            store[fullpath] = folderobj
                        
            if fullpath[-1] != '/':
                fullpath = fullpath+'/'
            
            # TODO: We need a way to assign the folders attribute to a folder.
            #folderobj.folders = []
 
            # I'm pretty sure this is obsolete code in this iteration but may be useful in the future.
            #for folder in folders:
            #    print folder
            #    subfolderstat = target.filesystem.stat(fullpath+folder)
            #    subfolderobj = File(folder,fullpath,subfolderstat,target,True)
            #    subfolderobj = runmodules(subfolderobj,target.filesystem)
            #    store[fullpath+'/'+folder] = subfolderobj
                
    
            # stat the files in that folder.
            for file in files:
                print file
                filestat = target.filesystem.stat(fullpath+file)
                # this file is in the folder we just found the position of with folderobj, so we can set its relpath to the folder object.
                fileobj = File(file, fullpath, filestat, target)
                fileobj = runmodules(fileobj,target.filesystem)
                store[fullpath+file] = fileobj
                

        # we ran out of folder objects
        except StopIteration:
            print "finished target " + target.tostring()
            break

        # A file or folder had an issue, keep going
        except:
            print "we encountered an error scanning " + target.tostring()
            import traceback
            print traceback.format_exc()

    # Commit
    transaction.commit()

    print "Gave up looking for work - dying"
    exit(0)


def signal_handler(signal, frame):
        # Ugh.
        global queue

        print " -- SIGINT DETECTED, FLUSHING TO DISK -- "
        transaction.commit()
        pdb.set_trace()


        # Todo: Save queue status
        ## snapshot the queue of targets
        #queue.close()
        #queue_snapshot = []
        #while not queue.empty():
        #    queue_snapshot.append(queue.get())
        ## save the queue to disk
        #with open('data/queue.tmp',w) as tmpqueue:
        #    tmpqueue.write(pickle.dumps(tmpqueue))
        ## Todo: we save the targets, their FS's, and therefore their file trees - we should be able to extrapolate what position we were at when we saved to disk using this info.

        print " -- Finished! -- "
        sys.exit()

    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    target_queue = []
    actions = []
    extensions = []
    fs_settings = {}

    # Settings housekeeping
    if settings.TARGET_LIST is None:
        print "You don't have a target list specified"
        exit()
    with open(settings.TARGET_LIST,'r') as target_list:
        targets = target_list.readlines()
        if len(targets)<1:
            print "You did not specify anything to scan in your target file."

    print "Loading ZODB storage and connection"
    # Warning: Globals loaded here
    storage = ZODB.FileStorage.FileStorage('data/mydata.fs')
    db_c = ZODB.DB(storage)
    connection = db_c.open()
    db = connection.root()


    #TODO: Make the collections a user-settable thing in case they need multiple "sites"
    # We want to emulate NEXPOSE's collections -- sites -> targets -> vulnerabilities
    #db['collection-1'] = {}
    #db = db['collection-1']

    print "Importing actions"
    actions = utils.loadmodules('plugins/actions')

    print "Importing extensions"
    extensions = utils.loadmodules('plugins/extensions')

    print "Importing Filesystems"
    filesystem_import_test = utils.loadmodules('filesystems')
    del filesystem_import_test

    print "Parsing Target File"
    # Parses the targeting file into target objects
    targets = targeting.targeter().parse()

    print "Scanning / Validating Targets"
    # Validation routine built into the Filesystem handlers -- verifies that the target is actually running the indicated filesystem
    # TODO: Portscan and find services we know we can handle.
    targets = [i for i in targets if i.validate() is not False]

    if len(targets)<1:
        print "No valid targets - exiting."
        exit(1)

    #debug mode only remove.
    for target in targets:
        scanprocess(None,target)

    # where the magic happens
    print "Scanning targets"
    thread_manager(targets)
