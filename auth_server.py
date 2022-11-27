#!/usr/bin/env python3

# First client sends message to auth server containing uname, pwd
# Stores in db and checks
# If credentials don't match, then reject the user
# If they match, forward to other servers (load balancing)

""""Creates and runs the server responsible for authentication and load balancing.

The host and port on which this server runs can be configured in `ports.py`.

All clients connect to this server at the beginning. After the clients signup or successfully login, this server redirects the clients to the one of the main servers, which is decided by the load balancer. 

The usernames and passwords are stored in the authdb database. This database can be accessed only by this server. Also, after signing up successfully, it creates a table for the username in the msg_storage database.

The authentication server uses the end2end module for encrypted communication with the clients.

Usage-
#. `sudo service postgresql start` : start the postgresql servers.
#. `sudo -u postgres psql -f cleaner.sql` : Creates the required databases on the postgres server and drops the databases with the same name, if any. So run this only the first time you run the auth_server.
#. `python3 auth_server.py` : this was tested using `python3.11`.
"""
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
sql_msg_cur = sql_msg_conn.cursor()

# create a table of public keys
sql_msg_cur.execute("""CREATE TABLE IF NOT EXISTS PUBKEYS(
            USERNAME TEXT PRIMARY KEY,
            PUBKEY TEXT
        )""")
sql_msg_conn.commit()

# create the server socket
auth_server = socket.socket()
auth_server.bind((host, port))
auth_server.listen(1)

#creates a separate thread for each client 
while True:
    Client, address = auth_server.accept()
    print ("connected")
    conn = threading.Thread(target=auth_client_handler.interact, args = (Client,sql_auth_conn, sql_msg_conn))
    conn.start()