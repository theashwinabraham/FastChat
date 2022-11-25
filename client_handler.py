import threading
import socket
import end2end
import json
# import sys
import time
# import psycopg2
# import rsa
from message import Message

# def parse_message(message):
#     l =  message.split("\n")
#     return [l[0], l[1]]

#class to handle the clients(to receive and distribute messages)
class client_handler:
    """Class for receiving, forwarding and sending messages to clients.
    """
    #stores the time interval after which the server checks for messages to be sent
    latency = 0.1
    #key which is used by the auth_server to recognize this as a server
    server_key = "7ng#$(b4Wpd!f7zM"

    #stores the otps corresponding to each client
    otp_dict = {}

    #stores all the active threads
    active_threads = dict()
    
    def __init__(self, name, client) :
        #stores the pending messages to be sent to each client
        """Constructor

        :param name: username of the client associated with the given object
        :type name: str
        :param client: connection with the client
        :type client: socket.socket
        """
        self.message_buffer = []
        self.client_name = name
        self.client = client
        self.isActive = True
        self.lock = threading.Lock()

    #waits and receives messages from the client
    def multi_threaded_client(self, connection: socket.socket, sql_msg_conn, sql_grp_conn):
        """Receives messages from the client.

        :param connection: connection with the client
        :type connection: socket.socket
        :param sql_msg_conn: connection with msg_storage
        :type sql_msg_conn: psycopg2.connection
        :param sql_grp_conn: connection with groupdb
        :type sql_grp_conn: psycopg2.connection
        """        
        # print('reached here')
        connection.sendall(str.encode('Server is working:'))
        # print("REACHED HERE")
        if not self.checkClientOtp(connection):
            return
        msg_cursor = sql_msg_conn.cursor()
        grp_cursor = sql_grp_conn.cursor()
        while True:
            # data = connection.recv(2048)
            data = Message.recv(connection)
            if not data:
                break
            print(data)
            data = json.loads(data.decode())  

            # First time when user tries to send a message to another user (DMs or group)
            if(data['action'] == 0):
                msg_cursor.execute("SELECT pubkey from pubkeys where username = %(username)s", {"username": data["receiver"]})

                pubkey = msg_cursor.fetchone()
                # print(pubkey)

                if pubkey:
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c':str(pubkey[0])}).encode())
                        Message.send(json.dumps({'c':str(pubkey[0])}).encode(), connection)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                else:
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c':"None"}).encode())
                        Message.send(json.dumps({'c':"None"}).encode(), connection)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                    continue

                # shared_key = connection.recv(2048)
                shared_key = Message.recv(connection)
                # print(shared_key)
                print(shared_key)
                if(shared_key != b"None"):
                    msg = {'k': shared_key.decode()}
                    msg = json.dumps(msg)
                    print(data['receiver'])

                    msg_cursor.execute("INSERT INTO " + data['receiver'] + " (time, message, username) VALUES (%(time)s, %(msg)s, %(user)s)".format(), {"time": time.time_ns(), 'msg':msg, 'user': self.client_name})
                    sql_msg_conn.commit()

            # Normal DMs (not first time)
            elif(data['action'] == 1):

                msg = {'m':data['message']}
                # msg = json.dumps(msg)
                # print(data['receiver'].rsplit("__"))
                if(data['receiver'].rfind("__") == -1):
                    msg = json.dumps(msg)
                    cmd = f"""INSERT INTO {data['receiver']} (time, message, username) VALUES ('{time.time_ns()}', '{msg}', '{self.client_name}')"""
                    # print(cmd)
                    msg_cursor.execute(cmd)
                    sql_msg_conn.commit()
                else:
                    msg['sender'] = self.client_name
                    msg = json.dumps(msg)
                    grp_cursor.execute("SELECT USERNAME FROM " + data['receiver'] + f" WHERE USERNAME != '{self.client_name}'")
                    L = grp_cursor.fetchall()
                    t = time.time_ns()
                    for users in L:
                        cmd = f"""INSERT INTO {users[0]} (time, message, username) VALUES ('{t}', '{msg}', '{data['receiver']}')"""
                        msg_cursor.execute(cmd)
                        sql_msg_conn.commit()
        
            elif(data['action'] == 4):
                # add to grp
                try:
                    grp_cursor.execute("SELECT ROLE FROM " + data['grp_name']+ f" WHERE USERNAME = '{self.client_name}' ")
                    L = grp_cursor.fetchall()
                    if not L[0][0]:
                        raise Exception()

                    grp_cursor.execute("INSERT INTO " + data['grp_name']+  " (USERNAME, ROLE) VALUES(%(user)s, '0')", { 'user':data["username"]})

                    msg_dict = {'km':data['key']}
                    msg_dict = json.dumps(msg_dict)
                    msg_cursor.execute(f"INSERT INTO {data['username']} (time, message, username) VALUES (%(time)s, %(msg)s, %(grp)s)", {"time": time.time_ns(), 'msg':msg_dict, 'grp': data['grp_name']})
                    sql_grp_conn.commit()
                    sql_msg_conn.commit()

                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c' : "1"}).encode()) 
                        Message.send(json.dumps({'c' : "1"}).encode(), connection)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                except Exception as e:
                    print(e)
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c' : "0"}).encode())
                        Message.send(json.dumps({'c' : "0"}).encode(), connection)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                
            elif(data['action'] == 5):
                # create grp
                try:
                    grp_cursor.execute(f"""CREATE TABLE {data['grp_name']}(
                        USERNAME TEXT PRIMARY KEY,
                        ROLE BOOLEAN 
                    )""") #role is 1 if the client is an admin and 0 if not
                    grp_cursor.execute(f"""INSERT INTO {data['grp_name']} (USERNAME, ROLE) VALUES ('{self.client_name}', '1')""")
                    sql_grp_conn.commit()
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c' : "1"}).encode())
                        Message.send(json.dumps({'c' : "1"}).encode(), connection) 
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                except Exception as e:
                    print(e)
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c' : "0"}).encode())
                        Message.send(json.dumps({'c' : "0"}).encode(), connection) 
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()

            elif(data['action'] == 7):
                # delete user from grp
                try:
                    grp_cursor.execute("SELECT ROLE FROM " + data['grp_name']+ f" WHERE USERNAME = '{self.client_name}' ")
                    L = grp_cursor.fetchall()
                    if (L[0][0] == False):
                        raise Exception()

                    grp_cursor.execute(f"DELETE FROM {data['grp_name']} WHERE username='{data['username']}';")
                    sql_grp_conn.commit()
                    
                    msg_dict = {'gd': data['grp_name']}
                    msg_dict = json.dumps(msg_dict)
                    msg_cursor.execute(f"INSERT INTO {data['username']} (time, message, username) \
                    VALUES (%(time)s, %(msg)s, %(grp)s)", {"time": time.time_ns(), 'msg':msg_dict, 'grp': data['grp_name']})
                    sql_msg_conn.commit()
                    
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c' : "1"}).encode())
                        Message.send(json.dumps({'c' : "1"}).encode(), connection)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                except Exception as e:
                    print(e)
                    self.lock.acquire()
                    try:
                        # connection.sendall(json.dumps({'c' : "0"}).encode())
                        Message.send(json.dumps({'c' : "0"}).encode(), connection)    
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
            elif data['action'] == 8:
                print("recieved file")
                msg = {'f':data['file_name']}
                file = Message.recv(connection)

                if(data['receiver'].rfind("__") == -1):
                    msg = json.dumps(msg)
                    msg_cursor.execute("INSERT INTO " + data['receiver'] + " (time, message, username, file) VALUES (%s, %s, %s, %s)", (time.time_ns(), msg, self.client_name, file))
                    sql_msg_conn.commit()
                else:
                    msg['sender'] = self.client_name
                    msg = json.dumps(msg)
                    grp_cursor.execute("SELECT USERNAME FROM " + data['receiver'] + f" WHERE USERNAME != '{self.client_name}'")
                    L = grp_cursor.fetchall()
                    t = time.time_ns()
                    for users in L:
                        msg_cursor.execute("INSERT INTO " + users[0] + " (time, message, username, file) VALUES (%s, %s, %s, %s)", (time.time_ns(), msg, data['receiver'], file))
                        sql_msg_conn.commit()
                
        print("closing the connection")
        self.isActive = False
        self.active_threads.pop(self.client_name)
        connection.close()
    #sends the messages to the client
    def send_messages(self, sql_msg_conn):
        """Sends messages from msg_storage to the clients.

        :param sql_msg_conn: connection with msg_storage
        :type sql_msg_conn: psycopg2.connection
        """
        cursor = sql_msg_conn.cursor()
        while self.isActive:
            # print(self.client_name)
            cursor.execute(f"SELECT time, message, username, file FROM {self.client_name} ORDER BY time ASC;")

            for msg in cursor.fetchall():
                print(msg)
                if msg[3]:
                    json_msg = json.loads(msg[1])
                    json_msg['time'] = msg[0]
                    json_msg['username'] = msg[2]
                    json_msg = json.dumps(json_msg)

                    self.lock.acquire()
                    try:
                        Message.send(json_msg.encode(), self.client)
                        Message.send(bytes(msg[3]), self.client)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                else:
                    json_msg = json.loads(msg[1])
                    json_msg['time'] = msg[0]
                    json_msg['username'] = msg[2]
                    json_msg = json.dumps(json_msg)
                    print(json_msg)
                    self.lock.acquire()
                    try:
                        # self.client.sendall(str.encode(json_msg))
                        Message.send(json_msg.encode(), self.client)
                    except Exception as e:
                        print(e)
                    finally:
                        self.lock.release()
                cursor.execute(f"DELETE FROM {self.client_name} WHERE time='{msg[0]}';")
                sql_msg_conn.commit()
                # time.sleep(1)
            time.sleep(self.latency)

    @classmethod
    def getClientName(cls, Client, sql_msg_conn, sql_grp_conn):
        print("getting client name", flush=True)
        name = bytes.decode(Client.recv(1024))
        obj = client_handler(name, Client)
        t = threading.Thread(target = client_handler.multi_threaded_client, args = (obj, Client, sql_msg_conn, sql_grp_conn))
        t.start()
        t1 = threading.Thread(target = client_handler.send_messages, args = (obj, sql_msg_conn))
        t1.start()
        client_handler.active_threads[name] = (obj, t, t1, Client)
        # print(client_handler.active_threads, flush=True)
    @classmethod
    def authServerInterface(cls, auth_host, auth_port, id, port):
        """Communicates with the auth_server

        :param auth_host: host on which the auth_server is running
        :type auth_host: str
        :param auth_port: port on which the auth_server is running
        :type auth_port: int
        :param id: server id
        :type id: int
        :param port: server port
        :type port: int
        """
        communicator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        communicator.connect((auth_host, auth_port))
        serverPayload = {'server_key':cls.server_key, 'id':id, 'port':port}
        serverPayload = json.dumps(serverPayload)
        communicator = end2end.createComunicator(communicator, 100)
        t = threading.Thread(target = client_handler.sendLoad, args = (communicator, ))
        t.start()
        communicator.send(bytes(serverPayload, "utf-8"))
        while(True):
            res = communicator.recv()
            if not res:
                break
            res = res.decode()
            assert(isinstance(res, str))
            res = json.loads(res)
            cls.otp_dict[res['username']] = res['otp']
    @classmethod
    def sendLoad(cls, communicator: end2end.Communicator):
        while(True):
            time.sleep(5)
            temp, Message.current_throughput = Message.current_throughput, 0
            communicator.send(str(temp).encode('utf-8'))

    def checkClientOtp(self, Client):
        res = Client.recv(1024)
        res = json.loads(res.decode())
        # print("res: ", res)
        # print(self.otp_dict)
        if res['otp'] == self.otp_dict[res['username']]:
            Client.send(b"1")
            self.otp_dict.pop(res['username'])
            return True
        else:
            Client.send(b"0")
            Client.close()
            self.active_threads.pop(self.client_name)
            self.otp_dict.pop(res['username'])
            return False
    
    