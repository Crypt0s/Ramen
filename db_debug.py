#!/usr/bin/python

#
#   Stub that sets up the DB so i can play with it in pdb
#
import ZODB, ZODB.FileStorage, pdb

storage = ZODB.FileStorage.FileStorage('mydata.fs')
db_c = ZODB.DB(storage)
connection = db_c.open()
db = connection.root()
db['collection-1'] = {}
db = db['collection-1']

pdb.set_trace()
