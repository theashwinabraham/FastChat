import socket
import json
import end2end
import ports
import random
import psycopg2

#IMPORTANT CHANGE:
# let each thread have its own cursor, cursors are not thread safe 
# ref: https://www.geeksforgeeks.org/python-psycopg-cursor-class/#:~:text=Cursors%20are%20not%20thread%2Dsafe,used%20by%20a%20single%20thread.

class auth_client_handler:
    host = '127.0.0.1'
    port = 10000
    ThreadCount = 0
    server_key = "7ng#$(b4Wpd!f7zM" #this is passed in the json object by the servers which are trying to connect with the auth_server
    #interact with the user
    @classmethod
    def interact(cls, Client, auth_connection, msg_connection):
        assert(isinstance(Client, socket.socket))
        auth_cursor = auth_connection.cursor()
        msg_cursor = msg_connection.cursor()
        Client = end2end.createComunicator(Client, 100)
        while True:
            auth_data = Client.recv()
            if not auth_data:
                break
            auth_data = json.loads(auth_data.decode("utf-8"))
            try:
                if auth_data['server_key'] == cls.server_key:
                    print(f"server {auth_data['id']} connected")
                    LoadBalancer.addServer(Client, auth_data['id'])
                    return
            except Exception:
                pass
            if(auth_data['action'] == 0):
                if auth_client_handler.validate_user(auth_cursor, auth_data):
                    T = LoadBalancer.getHostAndPort(auth_data['username'])
                    T = json.dumps(T)
                    Client.send(bytes(T , encoding= 'utf-8'))
                else:
                    Client.send(b"{}")
            elif(auth_data['action'] == 1):
                if auth_client_handler.addUser(auth_cursor, auth_data, msg_cursor):
                    T = LoadBalancer.getHostAndPort(auth_data['username'])
                    T = json.dumps(T)
                    Client.send(bytes(T , encoding= 'utf-8'))
                else:
                    Client.send(b"{}")
        print("connection closed")
        msg_connection.commit()
        auth_connection.commit()
    @classmethod
    def validate_user(cls, cursor, auth_data):
        cmd = "SELECT * FROM AUTH_DATA WHERE USERNAME = '{usr}'".format(usr = auth_data['username'])
        cursor.execute(cmd)
        data = cursor.fetchall()
        if (len(data) != 0):
            if (auth_data['password'] == data[0][1]):
                return True
        return False
    @classmethod
    def addUser(cls, cursor, auth_data, msg_cursor):
        # assert(isinstance(cursor, psycopg2.cursor))

        if( len(auth_data['username'])==0 or len(auth_data['password'])==0):
            return False

        cmd = "INSERT INTO AUTH_DATA (USERNAME, PASSWORD) VALUES ('{}', '{}')".format(auth_data['username'], auth_data['password'])
        print(cmd)
        try:
            cursor.execute(cmd)
        except Exception as e:
            print(e)
            return False

        msg_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {auth_data['username']}(
            timestamp TEXT PRIMARY KEY,
            message TEXT,
            username TEXT
        );""")

        return True
class LoadBalancer:
    Servers = []
    @classmethod
    def getHostAndPort(cls, username):
        #add code to distribute the client load optimally among servers
        host = ports.server_host
        port = ports.server_port
        otp = random.randint(10000, 99999)
        # print(cls.Servers)
        cls.Servers[0][0].send(bytes(json.dumps({'username':username, 'otp':otp}), "utf-8"))
        return {'host': host, 'port':port, 'otp': otp}
    @classmethod
    def addServer(cls, Client, id):
        cls.Servers.append((Client, id))