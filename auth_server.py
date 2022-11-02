# First client sends message to auth server containing uname, pwd
# Stores in db and checks
# If credentials don't match, then reject the user
# If they match, forward to other servers (load balancing)

import psycopg2
from threading import *
import socket
from auth_client_handler import *

#host and port
host = '127.0.0.1'
port = 10001
ThreadCount = 0

#connect to psycopg2
sql_conn = psycopg2.connect(database="authdb", user="ananth", password="ananth", host="127.0.0.1", port =  "5432")
sql_cur = sql_conn.cursor()
sql_cur
#create a database of usernames and passwords
# sql_cur.execute('''DROP TABLE AUTH_DATA''')
# sql_cur.execute('''
#     CREATE TABLE AUTH_DATA(
#     USERNAME TEXT PRIMARY KEY,
#     PASSWORD TEXT
# );''')
# sql_conn.commit()

#create the server socket
auth_server = socket.socket()
auth_server.bind((host, port))
auth_server.listen(1)

while True:
    Client, address = auth_server.accept()
    print ("connected")
    conn = Thread(target=auth_client_handler.interact, args = (Client,sql_cur))
    conn.start()