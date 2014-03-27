#!/usr/bin/python

#
#   Stub that sets up the DB so i can play with it in pdb
#
import ZODB, ZODB.FileStorage, pdb

storage = ZODB.FileStorage.FileStorage('mydata.fs')
db_c = ZODB.DB(storage)
connection = db_c.open()
db = connection.root()
# files represents where the actual file data is stored.  Remember we only use w_Root if we are writing to the db store.
files = db['127.0.0.1'].filesystems['local_disk'].root

print files.keys[0]

pdb.set_trace()
