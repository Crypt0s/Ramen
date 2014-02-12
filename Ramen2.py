#!/usr/bin/python

#
#   Ramen
#
#   Ramen is a (mostly) project designed to quickly and efficiently scan fileshares within Active Directory(ies) and map relationships between users and files.
#   It uses Python, cifsacl bindings, Psycopg2, Postgresql, PySMBC, and calls to shell in order to detect, mount, scan, map, and store servers, files, users, and file permissions.
#   This project is not (officially) affiliated with the open-source project "Noodle-ng", but it's functionality is similar and it helped me come up with a name.
#   
#

import multiprocessing, threading, os, settings,logging,random
import targeting
from multiprocessing import Pool,Queue
from multiprocessing.pool import ThreadPool
import ldap,pdb
import psycopg2
import utils
from cifsacl import *
from utils import fileattr
import targeting        


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

        ## DB CODE ############################################################################################################################################################
        try:
            conn_string = "host='%s' dbname='%s' user='%s' password='%s' port='%s'" % (settings.DB_HOST,settings.DB_NAME,settings.DB_USR,settings.DB_PASS,settings.DB_PORT)
            connection = psycopg2.connect(conn_string)
            try:
	            connection.autocommit = True
            except:
                    connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
        except:
            import traceback
            print traceback.format_exc()
            print "Connection with database failed."
            exit(1)
        ## END DB CODE ##########################################################################################################################################################

        # Scan the target
        # TODO: put the target info into the DB here
        print target.tostring()

        # build the state tree
        # walker.next() returns ('folderpath',[files,in,that,folder])
        walker = targetobj.filesystem.walk()        

        
        try:
            # grab the next batch of files from the next folder
            folder,files = walker.next()

            # stat the folder and save it
            folderstat = targetobj.filesystem.stat(folder)

            # stat the files in that folder.
            for file in files:            
                filestat = targetobj.filesystem.stat(file)
        # we ran out of folder objects
        except StopIteration:
            print "finished target " + targetobj.tostring()

        # something else happend
        except:
            print "we encountered an error scanning " + targetobj.tostring()



        # "folder" objects -- this is not going to fit every fs context is it?
        try:
            current_directory = walker.next()
        except:
            print "no permissions"
            continue

        subfolders = current_directory[1]
        path = current_directory[0]
        files = current_directory[2]

        srv_name = target.host

        # TODO: Maybe not combine these two
        share_name = target.service + ':' + target.info
            
        # Get the location ID and if for some reason it doesn't already exist, create it.
        try:
            cursor.execute('SELECT lid from shares WHERE server = %(server)s AND share = %(share)s',{'server':srv_name,'share':share_name})
            if cursor.rowcount == 0:
                cursor.execute('INSERT INTO shares VALUES(%(server)s,%(share)s) RETURNING lid',{'server':srv_name,'share':share_name})
        except psycopg2.IntegrityError:
            cursor.execute('SELECT lid from shares WHERE server = %(server)s AND share = %(share)s',{'server':srv_name,'share':share_name})
        lid = cursor.fetchone()[0]        
    
        try:
            result_array = []
            # Store each file and it's properties 
            for file in files:
                fullpath = path+'/'+file
                perms = target.filesystem.getfacl(fullpath)

                # Store filename and location
                cursor.execute('SELECT fid FROM files where filename=%(filename)s and lid=%(lid)s',{'lid':lid,'filename':fullpath})
                if cursor.rowcount == 0:
                    cursor.execute('INSERT INTO files values(%(lid)s,%(filename)s) RETURNING fid',{'lid':lid,'filename':fullpath})
                fid = cursor.fetchone()[0]

                result_array.append(fileattr(fullpath,target.filesystem.stat(fullpath),perms))

                # Store the perms
                # Store file permissions and usernames
                for perm in perms:
                    if perms == []:
                        break
                    # TODO: Implement this -- figure out how.
                    user_dict = {'domain':'test','username':perm[0]}
                    try:
                        cursor.execute('SELECT uid FROM users WHERE domain=%(domain)s AND username=%(username)s',user_dict)
                        if cursor.rowcount == 0:
                            cursor.execute('INSERT INTO users values(%(domain)s,%(username)s) RETURNING uid',user_dict)
                    except psycopg2.IntegrityError:
                        cursor.execute('SELECT uid FROM users WHERE domain=%(domain)s AND username=%(username)s',user_dict)
    
                    uid = cursor.fetchone()[0]
                    
                    cursor.execute('SELECT * FROM permissions WHERE uid = %(uid)s AND permission=%(permission)s AND fid=%(fid)s',{'permission':perm[1]+'/'+perm[2],'fid':fid,'uid':uid})
                    if cursor.rowcount == 0:
                        cursor.execute('INSERT INTO permissions VALUES(%(uid)s,%(permission)s,%(fid)s)',{'permission':perm[1]+'/'+perm[2],'fid':fid,'uid':uid})
                 
                # Plugins loading area
                # Actions
                for module in actions:
                    try:
                        [module.action(attr) for attr in result_array]
                    except:
                        print "Action failed"
                        import traceback
                        print traceback.format_exc()

                # Extensions    
                for attr in result_array:
                    for module in extensions:
                        try:
                            if module.__match__(attr):
                                module.action(attr)
                        except:
                            print "Extension Failed."
                            import traceback
                            print traceback.format_exc()

        except:
            print "Something weird happened"
            import traceback
            print traceback.format_exc()
            cursor.close()
            connection.close()
            [queue.put(path+'/'+a) for a in subfolders]
            pass
    
        # Save to disk
        connection.commit()
        cursor.close()
        connection.close()
    
        # Return subfolders for the directory we just scanned in so we can add them to the queue to be scanned
        subfolders = [path+'/'+a for a in subfolders]
        [queue.put(subfolder) for subfolder in subfolders]

    print "Gave up looking for work"
    exit(0)
    
if __name__ == '__main__':
    target_queue = []
    actions = []
    extensions = []

    # Settings housekeeping
    try:
        conn_string = "host='%s' dbname='%s' user='%s' password='%s' port='%s'" % (settings.DB_HOST,settings.DB_NAME,settings.DB_USR,settings.DB_PASS,settings.DB_PORT)
        connection = psycopg2.connect(conn_string)

        # Handles older versions of pyscopg2, python.  aka: I had to do this to get it to work on CENTOS 6, WTF
        try:
            connection.autocommit = True
        except:
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = connection.cursor()
    except:
        import traceback
	print conn_string
        print traceback.format_exc()
        print "Connection with database failed -- exiting"
        exit(1)

    if settings.TARGET_LIST is None:
        print "You don't have a target list specified"
        exit()
    with open(settings.TARGET_LIST,'r') as target_list:
        targets = target_list.readlines()
        if len(targets)>1:
            print "You did not specify anything to scan in your target file."
    if '/' != settings.MOUNT_LOCATION[-1]:
        settings.MOUNT_LOCATION = settings.MOUNT_LOCATION+'/'

    #try:
    #    utils.bind_domain()
    #except:
    #    import traceback
    #    print traceback.format_exc()
    #    print "Failed to bind to domain -- did you mess up your LDAP settings?"
    #    exit()

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
    # Validation routine built into the clients
    targets = [i for i in targets if i.validate() is not False]

    print "Scanning targets"
    folder_thread(valid_targets)
