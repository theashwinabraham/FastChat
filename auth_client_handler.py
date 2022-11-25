import socket
import json
import end2end
import ports
import random
import psycopg2
import threading
from message import Message
import time

#IMPORTANT CHANGE:
# let each thread have its own cursor, cursors are not thread safe 
# ref: https://www.geeksforgeeks.org/python-psycopg-cursor-class/#:~:text=Cursors%20are%20not%20thread%2Dsafe,used%20by%20a%20single%20thread.


class auth_client_handler:
    """Class implementing most of the functionality of the auth_server.
    """
    host = '127.0.0.1'
    port = 10000
    ThreadCount = 0
    server_key = "7ng#$(b4Wpd!f7zM" #this is passed in the json object by the servers which are trying to connect with the auth_server
    #interact with the user
    @classmethod
    def interact(cls, Client, auth_connection, msg_connection):
        """Gets the username and password from the client, verifies it and sends the host and port back to the client as decided by the load balancer.

        Args:
            Client (socket.socket): Socket connected with the client
            auth_connection (psycopg2.connection): connetion with the `authdb` database
            msg_connection (psycopg2.connection): connection with the msg_storage database
        """
        # assert(isinstance(Client, socket.socket))
        # auth_cursor = auth_connection.cursor()
        # msg_cursor = msg_connection.cursor()
        Client = end2end.createComunicator(Client, 100)
        while True:
            auth_data = Client.recv()
            if not auth_data:
                break
            auth_data = json.loads(auth_data.decode("utf-8"))
            try:
                if auth_data['server_key'] == cls.server_key:
                    print(f"server {auth_data['id']} connected")
                    LoadBalancer.addServer(Client, auth_data['id'], auth_data['port'])
                    return
            except Exception as e:
                print(e)
            if(auth_data['action'] == 0):
                if auth_client_handler.validate_user(auth_connection, auth_data):
                    T = LoadBalancer.getHostAndPort(auth_data['username'])
                    print(T)
                    T = json.dumps(T)
                    Client.send(bytes(T , encoding= 'utf-8'))
                else:
                    Client.send(b"{}")
            elif(auth_data['action'] == 1):
                if auth_client_handler.addUser(auth_connection, auth_data, msg_connection):
                    auth_connection.commit()
                    msg_connection.commit()
                    T = LoadBalancer.getHostAndPort(auth_data['username'])
                    print(T)
                    T = json.dumps(T)
                    Client.send(bytes(T , encoding= 'utf-8'))
                else:
                    Client.send(b"{}")
        print("connection closed")
        msg_connection.commit()
        auth_connection.commit()
    @classmethod
    def validate_user(cls, auth_connection, auth_data):
        """Validates the username and password sent by the client from the authdb database.

        Args:
            auth_connection (psycopg2.connection): connection with the `authdb` database
            auth_data (dict): contains the username and password to be verified

        Returns:
            bool: returns if the verification is successful
        """
        cursor = auth_connection.cursor()
        cmd = "SELECT * FROM AUTH_DATA WHERE USERNAME = '{usr}'".format(usr = auth_data['username'])
        cursor.execute(cmd)
        data = cursor.fetchall()
        if (len(data) != 0):
            if (auth_data['password'] == data[0][1]):
                return True
        return False
    @classmethod
    def addUser(cls, auth_connection, auth_data, msg_connection):
        """Adds a new user to the list of username and passwords. Also, it creates a table for the user in the msg_storage database.

        :param auth_connection: connection with authdb
        :type auth_connection: psycopg2.connection
        :param auth_data: username and password of the user
        :type auth_data: dict
        :param msg_connection: connection with msg_storage
        :type msg_connection: psycopg2.connection
        :return: Returns False if the username is already taken, True otherwise
        :rtype: bool
        """              
        # assert(isinstance(cursor, psycopg2.cursor))
        auth_cursor = auth_connection.cursor()
        msg_cursor = msg_connection.cursor()
        if( len(auth_data['username'])==0 or len(auth_data['password'])==0):
            return False

        cmd = "INSERT INTO AUTH_DATA (USERNAME, PASSWORD) VALUES ('{}', '{}')".format(auth_data['username'], auth_data['password'])
        print(cmd)
        try:
            auth_cursor.execute(cmd)
        except Exception as e:
            auth_connection.rollback()
            print(f'Error caught: {e}')
            return False

        msg_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {auth_data['username']}(
            time TEXT PRIMARY KEY,
            message TEXT,
            username TEXT,
            file BYTEA
        );""")

        msg_cursor.execute("INSERT INTO PUBKEYS (USERNAME, PUBKEY) VALUES (%(username)s, %(pubkey)s)", {'username':auth_data['username'], 'pubkey':auth_data['pubkey']})

        return True
    
class LoadBalancer:
    """Class used for load balancing among servers.
    """
    loads = {} #stores the loads on the servers
    servers = {} #stores the servers
    server_loads = {}
    @classmethod
    def getHostAndPort(cls, username, strategy=2):
        """Returns the host and port of the main server to which the client is to be redirected, based on the load balancing strategy. Also sends an otp to the server as well as the client, which is used for verification when the client connects again.

        :param username: username of the client
        :type username: str
        :return: dictionary containing the host, port and otp
        :rtype: dict
        """
        if not len(cls.servers.keys()): return False
        #add code to distribute the client load optimally among servers
        host = ports.server_host
        # mindex = cls.loads.index(min(cls.loads))
        if strategy == 0: # Random
            m_id = random.choice(cls.loads.keys())
        elif strategy == 1: # Min Load
            temp = cls.loads
            temp1 = min(temp.values())
            m_id = [key for key in temp if temp[key] == temp1][0]
        if strategy == 2: #redirect to the server with the least throughput
            temp = cls.server_loads
            temp1 = min(temp.values())
            temp2 = [key for key in temp if temp[key] == temp1]

            m_id = temp2[0]
            for i in temp2:
                if cls.loads[i] < cls.loads[m_id]:
                    m_id = i
        cls.loads[m_id] += 1
            
        otp = random.randint(10000, 99999)
        port = cls.servers[m_id][1]
        print(f'LOAD BALANCER GET: {cls.loads}, {cls.servers}')
        cls.servers[m_id][0].send(bytes(json.dumps({'username':username, 'otp':otp}), "utf-8"))
        return {'host': host, 'port':port, 'otp': otp}
    @classmethod
    def addServer(cls, server, id, port):
        """adds the server to the list of loads and servers.

        :param server: server connection
        :type server: end2end.Communicator
        :param id: server id
        :type id: int
        :param port: port number of the server
        :type port: int
        """
        print(f'LOAD BALANCER ADD: {cls.loads}, {cls.servers}')
        t = threading.Thread(target = LoadBalancer.updateLoad, args = (server, id))
        t.start()
        cls.loads[id] = 0
        cls.servers[id] = (server, port)
        cls.server_loads[id] = 0
    @classmethod
    def updateLoad(cls, communicator: end2end.Communicator, id: int):
        """Gets the loads on the servers

        :param server: connection with the server
        :type server: end2end.Communicator
        :param id: id of the server
        :type id: int
        """                
        while True:
            load = communicator.recv()
            if not load: break
            load = int(load.decode('utf-8'))
            cls.server_loads[id] = load
            print(cls.server_loads)