import socket
import json
import end2end

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
        Client = end2end.createComunicator(Client, 100)
        while True:
            auth_data = Client.recv()
            if not auth_data:
                break
            auth_data = json.loads(auth_data.decode("utf-8"))
            if(auth_data['action'] == 0):
                if auth_client_handler.validate_user(cursor, auth_data):
                    T = LoadBalancer.getHostAndPort()
                    T = json.dumps(T)
                    Client.send(bytes(T , encoding= 'utf-8'))
                else:
                    Client.send(b"{}")
            elif(auth_data['action'] == 1):
                if auth_client_handler.addUser(cursor, auth_data):
                    T = LoadBalancer.getHostAndPort()
                    T = json.dumps(T)
                    Client.send(bytes(T , encoding= 'utf-8'))
                else:
                    Client.send(b"{}")
        print("connection closed")
        connection.commit()

    def validate_user(cursor, auth_data):
        cmd = "SELECT * FROM AUTH_DATA WHERE USERNAME = '{usr}'".format(usr = auth_data['username'])
        cursor.execute(cmd)
        data = cursor.fetchall()
        if (len(data) != 0):
            if (auth_data['password'] == data[0][1]):
                return True
        return False

    def addUser(cursor, auth_data):
        # assert(isinstance(cursor, psycopg2.cursor))
        cmd = "INSERT INTO AUTH_DATA (USERNAME, PASSWORD) VALUES ('{}', '{}')".format(auth_data['username'], auth_data['password'])
        print(cmd)
        try:
            cursor.execute(cmd)
        except Exception as e:
            print(e)
            return False
        return True
class LoadBalancer:
    def getHostAndPort():
        host = '127.0.0.1'
        port = 9000
        return {'host': host, 'port':port}