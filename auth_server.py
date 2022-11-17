# First client sends message to auth server containing uname, pwd
# Stores in db and checks
# If credentials don't match, then reject the user
# If they match, forward to other servers (load balancing)

import psycopg2
import threading
import socket
from auth_client_handler import *
import ports

#host and port
host = ports.auth_server_host
port = ports.auth_server_port
ThreadCount = 0

#connect to psycopg2
sql_auth_conn = psycopg2.connect(database="authdb", user="ananth", password="ananth", host="127.0.0.1", port =  "5432")
sql_auth_cur = sql_auth_conn.cursor()
#create a table of usernames and passwords
sql_auth_cur.execute('''
    CREATE TABLE IF NOT EXISTS AUTH_DATA(
        USERNAME TEXT PRIMARY KEY,
        PASSWORD TEXT
        );
''')
sql_auth_conn.commit()

sql_msg_conn = psycopg2.connect(database="msg_storage", user="ananth", password="ananth", host="127.0.0.1", port =  "5432")

#create the server socket
auth_server = socket.socket()
auth_server.bind((host, port))
auth_server.listen(1)

while True:
    Client, address = auth_server.accept()
    print ("connected")
    conn = threading.Thread(target=auth_client_handler.interact, args = (Client,sql_auth_conn, sql_msg_conn))
    conn.start()