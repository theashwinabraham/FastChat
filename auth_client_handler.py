import psycopg2
import threading
import socket
import json

#IMPORTANT CHANGE:
# let each thread have its own cursor, cursors are not thread safe 
# ref: https://www.geeksforgeeks.org/python-psycopg-cursor-class/#:~:text=Cursors%20are%20not%20thread%2Dsafe,used%20by%20a%20single%20thread.

class auth_client_handler:
    host = '127.0.0.1'
    port = 10000
    ThreadCount = 0

    #interact with the user
    def interact(Client, connection):
        assert(isinstance(Client, socket.socket))
        cursor = connection.cursor()
        while True:
            auth_data = Client.recv(1024)
            if not auth_data:
                break
            auth_data = json.loads(auth_data.decode("utf-8"))
            if auth_client_handler.validate_user(cursor, auth_data):
                T = LoadBalancer.getHostAndPort()
                T = json.dumps(T)
                Client.send(bytes(T , encoding= 'utf-8'))
            else:
                Client.send(b"{}")
        print("connection closed")

    def validate_user(cursor, auth_data):
        cmd = "SELECT * FROM AUTH_DATA WHERE USERNAME = '{usr}'".format(usr = auth_data['username'])
        cursor.execute(cmd)
        data = cursor.fetchall()
        if (len(data) != 0):
            if (auth_data['password'] == data[0][1]):
                return True
        return False

class LoadBalancer:
    def getHostAndPort():
        host = '127.0.0.1'
        port = 9000
        return {'host': host, 'port':port}