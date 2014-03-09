#!/usr/bin/python

#
#   Ramen
#
#   Ramen is a (mostly) project designed to quickly and efficiently scan fileshares within Active Directory(ies) and map relationships between users and files.
#   It uses Python, cifsacl bindings, Psycopg2, Postgresql, PySMBC, and calls to shell in order to detect, mount, scan, map, and store servers, files, users, and file permissions.
#   This project is not (officially) affiliated with the open-source project "Noodle-ng", but it's functionality is similar and it helped me come up with a name.
#   
#
from file import File
import multiprocessing, threading, os, settings,logging,random
import targeting
from multiprocessing import Pool,Queue
from multiprocessing.pool import ThreadPool
import pdb
#import psycopg2
import ZODB, ZODB.FileStorage
import utils
import targeting        
import portscan

def folder_thread(target_queue):
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
        folder_thread([queue.get() for i in range(queue.qsize())])

def scanprocess(queue):

    # Cute little naming trick for debug only.
    name = random.randint(0,1000)
    while queue.qsize()>0:
        print str(name)+": looking for work"
        try:
            # the target is a tuple (targetobject,folder)
            target = queue.get(True,5)
            targetobj = target[0]
            folder = target[1]
        except:
            print "No work."
            exit(0)
        print str(name) +": Got some work : " + target

        # Scan the target
        # TODO: put the target info into the DB here
        print target.tostring()

        # build the state tree
        # walker.next() returns ('folderpath',[files,in,that,folder])
        walker = targetobj.filesystem.walk()
        
        try:
            # grab the next batch of files from the next folder
            fullpath,folders,files = walker.next()


            # parse and get the rel obj
            relpath = fullpath.split('/')
            # make sure that if the path was root (/) that we set it because the split strips single-slashes at the beginning.
            if relpath[0] == "":
                relpath[0] = '/'

            # load the target
            path = root[target]

            # WARNING: HERE BE BUGS (probably)
            # spider down the path options until the end and you will have reached the target folder
            for parentfolder in relpath:
                path = path[parentfolder]

            # stat the folder and save it
            folderstat = targetobj.filesystem.stat(folder)
            folderobj = File(folder,relpath,folderstat,target,True)
            
            # store this relative path thusly
            storage_path = root[target][path]
            # TODO: come up with way to test for list type or init a list if there isn't already one
            try:
                storage_path.append(folderobj)
            except:
                storage_path = [folderobj]

            # stat the files in that folder.
            for file in files:
                filestat = targetobj.filesystem.stat(fullpath+file)
                # this file is in the folder we just found the position of with folderobj, so we can set its relpath to the folder object.
                fileobj = File(file, folderobj, filestat, target, folder)
                root[target][path].append(fileobj)

        # we ran out of folder objects
        except StopIteration:
            print "finished target " + targetobj.tostring()
        except:
            print "we encountered an error scanning " + targetobj.tostring()

        # Plugins loading area
        # Actions
        for module in actions:
            try:
                module.action(file)
            except:
                print "Action failed"
                import traceback
                print traceback.format_exc()

        # Extensions    
        for attr in result_array:
            for module in extensions:
                try:
                    if module.__match__(file):
                        module.action(file)
                except:
                    print "Extension Failed."
                    import traceback
                    print traceback.format_exc()

    print "Gave up looking for work - dying"
    exit(0)
    
if __name__ == '__main__':
    target_queue = []
    actions = []
    extensions = []

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
    storage = ZODB.FileStorage.FileStorage('mydata.fs')
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root

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

    #print "Portscanning Targets"
    ## TODO: this is going to be slow as balls.  Make this fast as hell.
    ## results are saved in the target
    ## Also: throw the targets out if they don't have at least one open port to validate scannable services on.
    #targets = [i for i in targets if portscan.scan(i) is not False]

    print "Scanning / Validating Targets"
    # Validation routine built into the clients, uses the open ports detected by the portscanner
    targets = [i for i in targets if i.validate() is not False]

    if len(targets)<1:
        print "No valid targets - exiting."
        exit(1)

    # where the magic happens
    print "Scanning targets"
    folder_thread(targets)
