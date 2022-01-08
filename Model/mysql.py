# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 06:45:21 2020

@author: Ahmed
"""
import tensorflow

import MySQLdb

db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="ahmed19234",  # your password
                     db="graduation")        # name of the data base

# you must create a Cursor object. It will let
#  you execute all the queries you need
cur = db.cursor()
# Use all the SQL you like
cur.execute("""insert into objects values('ahmed','ahmed','ahmed',2.0,5.0)""")
# print all the first cell of all the rows

cur.execute("select * from objects where name='ahmed'")
for row in cur.fetchall():
    print( row)

db.close()




