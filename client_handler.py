import threading
import socket
import end2end
import json
import sys
import time
import psycopg2
import rsa

def parse_message(message):
    l =  message.split("\n")
    return [l[0], l[1]]

#class to handle the clients(to receive and distribute messages)
class client_handler:
    #stores the time interval after which the server checks for messages to be sent
    latency = 1
    #key which is used by the auth_server to recognize this as a server
    server_key = "7ng#$(b4Wpd!f7zM"
    #stores the id of the server
    server_id = int(sys.argv[1])
    #stores the otps corresponding to each client
    otp_dict = {}
    # #stores all the messages that are to be dispatched
    # message_dump = []
    #stores all the active threads
    active_threads = dict()
    def __init__(self, name, client) :
        #stores the pending messages to be sent to each client
        self.message_buffer = []
        self.client_name = name
        self.client = client
        self.isActive = True
        #create a new table for the user, if it hasn't been created yet
        # cursor = sql_connection.cursor()
        # cursor.execute(f"""CREATE TABLE IF NOT EXISTS {name}(
        #     TIME TIMESTAMP,
        #     MESSAGE TEXT, 
        #     USERNAME TEXT
        # )""")

    #waits and receives messages from the client
    def multi_threaded_client(self, connection: socket.socket, sql_msg_conn):
        connection.send(str.encode('Server is working:'))
        if not self.checkClientOtp(connection):
            return
        cursor = sql_msg_conn.cursor()
        while True:
            # try:
            data = connection.recv(2048)
            if not data:
                break
            print(data)
            data = json.loads(data.decode())  

            if(data['action'] == 0):
                cursor.execute("SELECT pubkey from pubkeys where username = %(username)s", {"username": data["receiver"]})

                pubkey = cursor.fetchone()
                # print(pubkey)
                if pubkey:
                    connection.sendall(str(pubkey[0]).encode())
                else:
                    connection.sendall("None".encode())
                    continue

                shared_key = connection.recv(2048)
                # print(shared_key)
                print(shared_key)
                
                msg = {'k': shared_key.decode()}
                msg = json.dumps(msg)
                print(data['receiver'])
                # cmd = f"""INSERT INTO {data['receiver']} (time, message, username) VALUES (to_timestamp({time.time()}), '{msg}', '{self.client_name}')"""
                cursor.execute("INSERT INTO " + data['receiver'] + " (time, message, username) VALUES (to_timestamp(%(time)s), %(msg)s, %(user)s)".format(), {"time": time.time(), 'msg':msg, 'user': self.client_name})
                sql_msg_conn.commit()

            elif(data['action'] == 1):

            # L = parse_message(data.decode('utf-8'))
            # L.append(self.client_name)
            # # self.message_dump.append(L)
            # # print(self.message_dump)
                msg = {'m':data['message']}
                msg = json.dumps(msg)
                cmd = f"""INSERT INTO {data['receiver']} (time, message, username) VALUES (to_timestamp({time.time()}), '{msg}', '{self.client_name}')"""
                # print(cmd)
                cursor.execute(cmd)
                sql_msg_conn.commit()
            # except Exception as e:
            #     print(e)

        print("closing the connection")
        self.isActive = False
        self.active_threads.pop(self.client_name)
        connection.close()
    #sends the messages to the client
    def send_messages(self, sql_msg_conn):
        cursor = sql_msg_conn.cursor()
        while self.isActive:
            # print(self.client_name)
            cursor.execute(f"SELECT time, message, username FROM {self.client_name};")

            for msg in cursor.fetchall():
                # print("msg", msg[:10])

                json_msg = json.loads(msg[1])
                json_msg['time'] = msg[0]
                json_msg['username'] = msg[2]
                json_msg = json.dumps(json_msg)
                print(json_msg)
                self.client.sendall(str.encode(json_msg))
                cursor.execute(f"DELETE FROM {self.client_name} WHERE time='{msg[0]}';")
                sql_msg_conn.commit()

            time.sleep(self.latency)
            # if(self.message_buffer != []):
            #     while len(self.message_buffer):
            #         print("Message from the display_message thread: ", self.message_buffer[0])
            #         self.active_threads[self.message_buffer[0][0]][3].sendall(str.encode(self.message_buffer[0][2] + "\n" + self.message_buffer[0][1]))
            #         self.message_buffer = self.message_buffer[1:]
    # @classmethod
    # def distribute_messages(cls):
    #     while True:
    #         while len(cls.message_dump):
    #             try:
    #                 print(len(cls.message_dump))
    #                 print(cls.message_dump[0], flush=True)
    #                 cls.active_threads[cls.message_dump[0][0]][0].message_buffer.append(cls.message_dump[0])
    #             except Exception as e:
    #                 print(e)
    #             cls.message_dump = cls.message_dump[1:]
    @classmethod
    def getClientName(cls, Client, sql_msg_conn):
        print("getting client name", flush=True)
        name = bytes.decode(Client.recv(1024))
        obj = client_handler(name, Client)
        t = threading.Thread(target = client_handler.multi_threaded_client, args = (obj, Client, sql_msg_conn))
        t.start()
        t1 = threading.Thread(target = client_handler.send_messages, args = (obj, sql_msg_conn))
        t1.start()
        client_handler.active_threads[name] = (obj, t, t1, Client)
        # print(client_handler.active_threads, flush=True)
    @classmethod
    def authServerInterface(cls, auth_host, auth_port):
        communicator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        communicator.connect((auth_host, auth_port))
        serverPayload = {"server_key":cls.server_key, 'id':cls.server_id}
        serverPayload = json.dumps(serverPayload)
        communicator = end2end.createComunicator(communicator, 100)
        communicator.send(bytes(serverPayload, "utf-8"))
        while(True):
            res = communicator.recv()
            if not res:
                break
            res = res.decode()
            assert(isinstance(res, str))
            res = json.loads(res)
            cls.otp_dict[res['username']] = res['otp']
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