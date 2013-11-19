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

from multiprocessing import Pool,Queue
from multiprocessing.pool import ThreadPool
import ldap,pdb
import psycopg2
import utils
from cifsacl import *

def folder_thread(folder_queue):
    queue = multiprocessing.Queue()
    [queue.put(folder) for folder in folder_queue]
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
    name = random.randint(0,1000)
    # Note: It may be faster (at the expense of memory) to push the ad bind object to the scanprocess if it's fork() safe...
    ad = utils.bind_domain()

    while queue.qsize()>0:
        print str(name)+": looking for work"
        try:
            folder = queue.get(True,5)
        except:
            print "No work."
            exit(0)
        print str(name) +": Got some work : " + folder
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
    
        # Scan the folder
        walker = os.walk(folder)
        try:
            current_directory = walker.next()
        except:
            print "no permissions"
            continue
        subfolders = current_directory[1]
        path = current_directory[0]
        files = current_directory[2]
    
        # Remove the mount location prefix from the mount path, grabbing the server name and the share name.
        prefix = len(settings.MOUNT_LOCATION.split('/'))
        splitpath = path.split('/')
    
        srv_name = splitpath[prefix-1]
        share_name = splitpath[prefix]
    
        try:
            # Get the LID -- this is a tradeoff that sacrifices speed for code maintainability
            cursor.execute('SELECT lid from shares WHERE server = %(server)s AND share = %(share)s',{'server':srv_name,'share':share_name})
            if cursor.rowcount == 0:
                cursor.execute('INSERT INTO shares VALUES(%(server)s,%(share)s) RETURNING lid',{'server':srv_name,'share':share_name})
        except psycopg2.IntegrityError:
            cursor.execute('SELECT lid from shares WHERE server = %(server)s AND share = %(share)s',{'server':srv_name,'share':share_name})
        lid = cursor.fetchone()[0]        
    
        try:
            # Store each file and it's properties 
            for file in files:
                fullpath = path+'/'+file
                # Get Permissions and SIDs from AD, then resolve the SID into Canonical Names
                perms = utils.resolve(ad,getfacl(fullpath))
                # Store filename and location
                cursor.execute('SELECT fid FROM files where filename=%(filename)s and lid=%(lid)s',{'lid':lid,'filename':fullpath})
                if cursor.rowcount == 0:
                    cursor.execute('INSERT INTO files values(%(lid)s,%(filename)s) RETURNING fid',{'lid':lid,'filename':fullpath})
                fid = cursor.fetchone()[0]
    
                # Store file permissions and usernames
                for perm in perms:
                    if perms == []:
                        break
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
    folder_queue = []
    mount_queue = []
    share_list = {}

    # Logging
    multiprocessing.log_to_stderr()

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

    try:
        utils.bind_domain()
    except:
        import traceback
        print traceback.format_exc()
        print "Failed to bind to domain -- did you mess up your LDAP settings?"
        exit()


    # This is where we should enter the main loop for a 'daemonized' version of this app.
    # I'll reserve that for a bit since I need to look into doing this "right"

    # Handles any network ranges in the target list.
    expanded_range = []
    for item in targets:
        if '/' in item:
            expanded_range = expanded_range + utils.ip_expand(item)
            targets.remove(item)
    targets = targets + expanded_range

    print "Checking for SMB servers on target hosts"
    # remove targets from the target list that aren't running the SMB server process.
    poolz = Pool(50)
    valid_targets = poolz.map(utils.checkSMB,targets)
    poolz.close()
    poolz.join()

    # This is a neat tidbit for editing a list in-place
    valid_targets[:] = (x for x in valid_targets if x is not None)

    print str(len(valid_targets))+" Valid targets found."
    del targets

    print "Finished scanning"
    for target in valid_targets:
        share_list.update(utils.list_shares(target))

    print "Found " + str(len(share_list.values())) + " Shares to scan"

    mount_array = []

    for server in share_list.keys():
        for share in share_list[server]:
            # Remove the location from the DB -- if we're re-scanning it, we want new values
            # TODO: Don't do this -- make the DB searchable by date?  Or maybe make a new table/DB for each scan?  That seems like a lot of overhead.
            cursor.execute("DELETE FROM shares WHERE server=%(server)s AND share=%(share)s",{'server':server,'share':share})

            # Block mount operation if we have hit the limit of mounts
            mountpoint = utils.mount(server,share)            
            mount_array.append(mountpoint)
            if len(mount_array)>=settings.MOUNT_LIMIT or share == share_list[share_list.keys()[-1]][-1] and len(mount_array)!=0:
                # Scan the batch -- blocks until done for the batch
                folder_thread(mount_array)
                # Unmount the batch
                print "Reached limit or last entry -- starting scan batch"
                for mountpoint in mount_array:
                    utils.umount(mountpoint)
                    mount_array.remove(mountpoint)
                print "Finished scan batch"
