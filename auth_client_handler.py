from pickle import FALSE, TRUE
from wsgiref import validate
import psycopg2
import threading
import socket
import json

#IMPORTANT CHANGE: let each thread have its own cursor, cursors are not thread safe 

class auth_client_handler:
    host = '127.0.0.1'
    port = 10000
    ThreadCount = 0

    #interact with the user
    def interact(Client, cursor):
        assert(isinstance(Client, socket.socket))
        while True:
            auth_data = Client.recv(1024)
            if not auth_data:
                break
            auth_data = json.loads(auth_data.decode("utf-8"))
            if auth_client_handler.validate_user(cursor, auth_data):
                Client.send(b"Successfully logged in")
            else:
                Client.send(b"Wrong credentials")
        print("connection closed")
    def validate_user(cursor, auth_data):
        cmd = "SELECT * FROM AUTH_DATA WHERE USERNAME = '{usr}'".format(usr = auth_data['username'])
        cursor.execute(cmd)
        data = cursor.fetchall()
        print(data)
        print(len(data))
        if (len(data) != 0) and (auth_data['password'] == data[1]):
            return True
        return False

