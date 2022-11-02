# First client sends message to auth server containing uname, pwd
# Stores in db and checks
# If credentials don't match, then reject the user
# If they match, forward to other servers (load balancing)

import psycopg2
import threading
import socket

#host and port
host = '127.0.0.1'
port = 10000
ThreadCount = 0

#connect to psycopg2
sql_conn = psycopg2.connect(database="authdb", user="ananth", password="ananth", host="127.0.0.1", port =  "5432")
sql_cur = sql_conn.cursor()

#create a database of usernames and passwords
sql_cur.execute('''
    CREATE TABLE AUTH_DATA(
    USERNAME TEXT PRIMARY KEY,
    PASSWORD TEXT
);''')
sql_conn.commit()

#create the server socket
auth_server = socket.socket
auth_server.listen(1)

