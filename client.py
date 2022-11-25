#!/usr/bin/env python3

"""Implementation of the client side
"""

import socket
import threading
# import psycopg2
import json 
import end2end
import ports
import rsa
from cryptography.fernet import Fernet
import time
import base64
from message import Message
from os.path import exists
import os.path
import os
import sys
# imports for the UI
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Header, Footer
from textual.reactive import reactive
# print(sys.version)
import traceback

# stores the keys for encryption
keys = {}
#lock for managing access to the keys dictionary
dict_lock = threading.Lock()

def verify_with_server(username, password, server):
    """Verifies the username and password entered by the user during login with the auth_server.

    :param username: username of the client
    :type username: str
    :param password: password of the client
    :type password: str
    :param server: connection with the auth_server
    :type server: socket.socket
    :return: returns false if the authentication fails, returns the details of the main server otherwise
    :rtype: bool or dict
    """
    assert(isinstance(server, socket.socket))
    global pubkey
    global privkey
    global keys
    server = end2end.createComunicator(server, 100)
    auth_data = {"username": username, "password": password, 'action':0}
    auth_data = json.dumps(auth_data)
    server.send(bytes(auth_data, encoding='utf-8'))
    data = server.recv()
    data = json.loads(data)
    if(data == {}):
        print("authentication failed")
        return False
    else:
        with open(f"{username}_keys.json", 'r') as key_file:
            keys = json.load(key_file)
            pubkey = rsa.PublicKey._load_pkcs1_pem(keys['pubkey'])
            privkey = rsa.PrivateKey._load_pkcs1_pem(keys['privkey'])
        return data

def add_to_server(username, password, server):
    """Sends the username and the password of the new client with the auth_server.

    :param username: username of the client
    :type username: str
    :param password: password of the client
    :type password: str
    :param server: connection with the auth_server
    :type server: end2end.Communicator
    :return: returns false if the username is already taken, returns the details of the main server otherwise
    :rtype: bool or dict
    """
    # assert(isinstance(server, socket.socket))
    #generating the rsa keys
    global pubkey
    global privkey
    global keys

    # send login id, password, and public key to server
    pubkey, privkey = rsa.newkeys(1024, poolsize=8)
    # server = end2end.createComunicator(server, 100)
    auth_data = {"username": username, "password": password, 'action':1, 'pubkey': (pubkey.save_pkcs1(format = "PEM").decode())}
    auth_data = json.dumps(auth_data)
    server.send(bytes(auth_data, encoding='utf-8'))

    # recieve the adress, otp, etc of server that it needs to connect incase of succesfull signup
    data = server.recv()
    data = json.loads(data)
    if(data == {}):
        return False
    else:
        keys['pubkey'] = pubkey.save_pkcs1(format = "PEM").decode()
        keys['privkey'] = privkey.save_pkcs1(format = "PEM").decode()
        with open(f"{username}_keys.json", 'w') as key_file:
            key_file.write(json.dumps(keys))
        return data    

def authenticate(server):
    """Takes the username and password from the user and calls the `add_to_server` and `verify_with_server` depending on whether the client wants to sign up or login.

    :param server: connection with the server
    :type server: socket.socket
    :return: dictionary containing the username, password and the dictionary obtained from the auth_server.
    :rtype: tuple
    """
    assert(isinstance(server, socket.socket))
    choice = input("Press 0 for login and 1 for signup: ")
    if choice == "1":
        server1 = end2end.createComunicator(server, 100)
        while True:
            username = input("Enter username: ")
            password = input("Enter password: ")
            res = add_to_server(username, password, server1)
            if not res:
                print("The entered username is not available")
                continue
            else:
                return (res, username, password)            
    else:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        return (verify_with_server(username, password, server), username, password)

def send_message(msg: str, receiver: str, Client: socket.socket) -> bool:
    """Sends the message to the messaging server (servers except the auth_server).

    :param msg: message to be sent
    :type msg: str
    :param receiver: username of the receiver of the message
    :type receiver: str
    :param Client: connection with the server
    :type Client: socket.socket
    :return: Returns True if the message was successfully sent, false otherwise
    :rtype: bool
    """
    if receiver in keys.keys():
        global fernet_key
        fernet_key = keys[receiver]
        fernet_key = base64.b64decode(fernet_key.encode())
    else:
        request = {"receiver": receiver, "action": 0}
        # Client.sendall(json.dumps(request).encode())
        Message.send(json.dumps(request).encode(), Client)

        # recv_pubkey = Client.recv(2048)
        while (input_box.communicator_buffer == -1):
            time.sleep(0.1)
        recv_pubkey = input_box.communicator_buffer
        input_box.communicator_buffer = -1
        # print(recv_pubkey)
        if recv_pubkey.decode() == "None":
            return False
    
        recv_pubkey = rsa.PublicKey._load_pkcs1_pem(recv_pubkey)

        fernet_key = Fernet.generate_key()
        b64_fernet_key = base64.b64encode(fernet_key)

        dict_lock.acquire()
        if receiver in keys.keys():
            fernet_key = base64.b64decode(keys[receiver].encode())
            Message.send(b"None" ,Client)
        else:
            keys[receiver] = b64_fernet_key.decode()
            
            # assert(fernet_key.decode().encode() == fernet_key)
            encrypted_key = base64.b64encode(rsa.encrypt(b64_fernet_key, recv_pubkey))
            # print("encrypted key: ", encrypted_key)
            # Client.sendall(encrypted_key)
            Message.send(encrypted_key, Client)

            with open(f"{username}_keys.json", 'w') as key_file:
                key_file.write(json.dumps(keys))
        dict_lock.release()

    f = Fernet(fernet_key)
    encoded_msg = f.encrypt(msg.encode('utf-8'))
    msg_dict = {"receiver": receiver, "message": encoded_msg.decode('utf-8'), "action": 1}
    # Client.sendall(json.dumps(msg_dict).encode('utf-8'))
    Message.send(json.dumps(msg_dict).encode(), Client)
    return True

def send_file(file_name: str, receiver: str, Client: socket.socket) -> bool:
    """Sends a file to the server.

    :param file_name: name of the file to be sent
    :type file_name: str
    :param receiver: username of the receiver
    :type receiver: str
    :param Client: connection with the server
    :type Client: socket.socket
    :return: returns True if the file was sent successfully
    :rtype: bool
    """
    if not exists(file_name): return False

    if receiver in keys.keys():
        global fernet_key
        fernet_key = keys[receiver]
        fernet_key = base64.b64decode(fernet_key.encode())
    else:
        request = {"receiver": receiver, "action": 0}
        # Client.sendall(json.dumps(request).encode())
        Message.send(json.dumps(request).encode(), Client)

        # recv_pubkey = Client.recv(2048)
        while (input_box.communicator_buffer == -1):
            time.sleep(0.1)
        recv_pubkey = input_box.communicator_buffer
        input_box.communicator_buffer = -1
        # print(recv_pubkey)
        if recv_pubkey.decode() == "None":
            return False
    
        recv_pubkey = rsa.PublicKey._load_pkcs1_pem(recv_pubkey)

        fernet_key = Fernet.generate_key()
        b64_fernet_key = base64.b64encode(fernet_key)

        dict_lock.acquire()
        if receiver in keys.keys():
            fernet_key = base64.b64decode(keys[receiver].encode())
            Message.send(b"None", Client)
        else:
            keys[receiver] = b64_fernet_key.decode()
            
            # assert(fernet_key.decode().encode() == fernet_key)
            encrypted_key = base64.b64encode(rsa.encrypt(b64_fernet_key, recv_pubkey))
            # print("encrypted key: ", encrypted_key)
            # Client.sendall(encrypted_key)
            Message.send(encrypted_key, Client)

            with open(f"{username}_keys.json", 'w') as key_file:
                key_file.write(json.dumps(keys))
        dict_lock.release()

    f = Fernet(fernet_key)
    encoded_msg = f.encrypt(file_name.encode())
    msg_dict = {"receiver": receiver, "file_name": encoded_msg.decode(), "action": 8}
    Message.send(json.dumps(msg_dict).encode(), Client)

    with open(file_name, "rb") as file_obj:
        file = file_obj.read()
        encryped_file = f.encrypt(base64.b64encode(file))
        Message.send(encryped_file, Client)

    return True

def add_to_grp(grp_name, new_user, Client: socket.socket) -> bool:
    """Adds another participant to a group. Can be done only by the admin of the group.

    :return: Returns True if the person is added, false otherwise.
    :rtype: bool
    """

    # if "__grp__" + grp_name not in keys.keys():
    #     return False

    grp_fernet_key = ""
    for grp in keys.keys():
        if(grp.rfind("__") == -1): continue

        if(grp.split("__", 1)[1] == grp_name):
            grp_fernet_key = keys[grp]
            grp_name =  grp
            break
    if(grp_fernet_key == ""):
        return False

    user_fernet_key = ""
    if new_user in keys.keys():
        user_fernet_key = keys[new_user]
        user_fernet_key = base64.b64decode(user_fernet_key.encode())
    else:
        request = {"receiver": new_user, "action": 0}
        # Client.sendall(json.dumps(request).encode())
        Message.send(json.dumps(request).encode(), Client)

        # recv_pubkey = Client.recv(2048)
        while (input_box.communicator_buffer == -1):
            time.sleep(0.1)
        recv_pubkey = input_box.communicator_buffer
        input_box.communicator_buffer = -1

        if recv_pubkey.decode() == "None":
            return False
    
        recv_pubkey = rsa.PublicKey._load_pkcs1_pem(recv_pubkey)

        user_fernet_key = Fernet.generate_key()
        b64_fernet_key = base64.b64encode(user_fernet_key)

        dict_lock.acquire()
        if new_user in keys.keys():
            user_fernet_key = base64.b64decode(user_fernet_key.encode())
            Message.send("None", Client)
        else:
            keys[new_user] = b64_fernet_key.decode()
            
            # assert(fernet_key.decode().encode() == fernet_key)
            encrypted_key = base64.b64encode(rsa.encrypt(b64_fernet_key, recv_pubkey))
            # print("encrypted key: ", encrypted_key)
            # Client.sendall(encrypted_key)
            Message.send(encrypted_key, Client)

            with open(f"{username}_keys.json", 'w') as key_file:
                key_file.write(json.dumps(keys))
        dict_lock.release()
    
    user_f = Fernet(user_fernet_key)

    encrypted_key = user_f.encrypt(grp_fernet_key.encode())

    msg_dict = {"grp_name": grp_name, "username": new_user, "key": encrypted_key.decode('utf-8'), "action": 4}
    msg_dict = json.dumps(msg_dict).encode()
    # Client.sendall(msg_dict)
    Message.send(msg_dict, Client)

    # res = Client.recv(2048)
    while (input_box.communicator_buffer == -1):
        time.sleep(0.1)
    res = input_box.communicator_buffer
    input_box.communicator_buffer = -1

    if (res.decode() == "1"):
        return True
    else:
        return False

def del_from_grp(grp_name, del_user, Client: socket.socket) -> bool:
    """Removes a participant from a group. Can be done only by the admin of the group.

    :return: Returns True if the person is added, false otherwise.
    :rtype: bool
    """
    found = False
    for grp in keys.keys():
        if(grp.rfind("__") == -1): continue

        if(grp.split("__", 1)[1] == grp_name):
            found = True
            grp_name =  grp
            break
    if not found:
        return False

    msg_dict = {"grp_name": grp_name, "username": del_user, "action": 7}
    msg_dict = json.dumps(msg_dict).encode()
    # Client.sendall(msg_dict)
    Message.send(msg_dict, Client)
    
    # res = Client.recv(2048)
    while (input_box.communicator_buffer == -1):
        time.sleep(0.1)
    res = input_box.communicator_buffer
    input_box.communicator_buffer = -1

    if (res.decode() == "1"):
        return True
    else:
        return False

def make_grp(grp_name: str, Client: socket.socket) -> bool:
    """Creates a group.

    :param grp_name: name of the group to be created
    :type grp_name: str
    :param Client: connection with the server
    :type Client: socket.socket
    :return: returns True if the group was created successfully
    :rtype: bool
    """
    # groups in the format username__groupname stored in keys

    grp_name = username + "__" + grp_name
    if grp_name in keys.keys():
        return False
    
    msg_dict = {'action' : 5, 'grp_name': grp_name}
    msg_dict = json.dumps(msg_dict).encode()

    # Client.sendall(msg_dict)
    Message.send(msg_dict, Client)

    # res = Client.recv(2048)
    while (input_box.communicator_buffer == -1):
        time.sleep(0.1)
    res = input_box.communicator_buffer
    input_box.communicator_buffer = -1

    if (res.decode() == "1"):
    
        grp_fernet_key = Fernet.generate_key()
        b64_grp_fernet_key = base64.b64encode(grp_fernet_key)
        dict_lock.acquire()
        keys[grp_name] = b64_grp_fernet_key.decode()
   
        with open(f"{username}_keys.json", 'w') as key_file:
            key_file.write(json.dumps(keys))
        dict_lock.release()
        return True
    else:
        return False

# establishing connection with auth server
Client = socket.socket()
host = '127.0.0.1'
try:
    port = ports.auth_server_port
    Client.connect((host, port))
except socket.error as e:
    print(f'Could not connect to the auth_server: {e}')
    exit(-1)

# authenticating and getting otp for subsequent server connection
res = authenticate(Client)
data, username, password = res
if not data:
    exit(-1)
host, port, otp = (data['host'], data['port'], data['otp'])
Client.close() # closing that connection
time.sleep(1)

if not exists("msg_log"): os.makedirs("msg_log")
log_txt = open(f'log_{username}.txt', 'w')
msg_log_txt = open(f'msg_log/log_{username}.txt', 'w')

#connect to the new server
Client = socket.socket()
try:
    Client.connect((host, port))
except socket.error as e:
    print(f"Can't connect to server: {e}")
    exit(-1)
Client.sendall(bytes(username, "utf-8")) # sending username to server

# print(host, port, otp)

Client.recv(1024)

payload = json.dumps({'username':username, 'otp':otp})

Client.send(bytes(payload, "utf-8"))
res = Client.recv(1024)
res = res.decode()
if res == "0":
    print("Connection unsuccessful")
    exit(-1)


#User interface
class input_box(Widget):
    """Widget displaying the messages in the textual interface
    """
    messages = reactive("")
    msg = ""
    communicator_buffer = -1
    #renders the text on the screen
    def render(self) -> str:
        return self.messages
    #receives messages from the server
    def receive_messages(self, Client: socket.socket) -> None:
        """Receives messages from the server and displays them.

        :param Client: connection with the server
        :type Client: socket.socket
        """
        while True:
            # res = Client.recv(2048)
            res = Message.recv(Client)
            if not res:
                break
            res = res.decode()
            log_txt.write(res + "\n")
            log_txt.flush()
            res = json.loads(res)
            try:
                if 'k' in res.keys():
                    recvd_key = rsa.decrypt(base64.b64decode(res['k'].encode()), privkey).decode()
                    dict_lock.acquire()
                    if res['username'] in keys.keys():
                        if recvd_key > keys[res['username']]:
                            keys[res['username'] + "_temp"] = recvd_key
                        elif recvd_key < keys[res['username']]:
                            keys[res['username'] + "_temp"] = keys[res['username']]
                            keys[res['username']] = recvd_key
                    else:
                        keys[res['username']] = recvd_key
                    with open(f"{username}_keys.json", 'w') as key_file:
                        key_file.write(json.dumps(keys))
                    dict_lock.release()
                    self.messages = "connected to user "+ res["username"] + "\n" + self.messages

                elif 'km' in res.keys():
                    f = Fernet(base64.b64decode(keys[res['username'].split('__')[0]].encode('utf-8')))
                    decoded_key = f.decrypt(res['km']).decode()
                    keys[res['username']] = decoded_key
                    self.messages = "added to group "+ res["username"].split('__')[1]  + "\n" + self.messages
                    # print(decoded_msg)
                    # self.messages = res["username"] + " sent: " + decoded_key + "\n" + self.messages
                    with open(f"{username}_keys.json", 'w') as key_file:
                        key_file.write(json.dumps(keys))

                elif 'm' in res.keys():

                    decoded_msg = ""
                    dict_lock.acquire()
                    if res['username'] + "_temp" in keys.keys():
                        f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                        try:
                            decoded_msg = f.decrypt(res['m']).decode()
                            del keys[res['username'] + "_temp"]
                            with open(f"{username}_keys.json", 'w') as key_file:
                                key_file.write(json.dumps(keys))
                        except:
                            f = Fernet(base64.b64decode(keys[res['username'] + "_temp"].encode('utf-8')))
                            decoded_msg = f.decrypt(res['m']).decode()
                    else:
                        f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                        decoded_msg = f.decrypt(res['m']).decode()
                    dict_lock.release()

                    # print(decoded_msg)
                    if 'sender' in res.keys():
                        self.messages = res['username'].split("__")[1] +": " + res["sender"] + " sent: " + decoded_msg + "\n" + self.messages

                    else:
                        self.messages = res["username"] + " sent: " + decoded_msg + "\n" + self.messages

                elif 'gd' in res.keys():
                    # delete from group
                    del keys[res['username']]
                    with open(f"{username}_keys.json", 'w') as key_file:
                        key_file.write(json.dumps(keys))
                    self.messages = "removed from grp " + res["username"].split('__')[1] + "\n" + self.messages
                        
                elif 'c' in res.keys():
                    input_box.communicator_buffer = res['c'].encode()
                    log_txt.write(res['c'] + "\n")
                    log_txt.flush()
                elif 'f' in res.keys():
                    dict_lock.acquire()
                    f = None
                    file_name = "thisShouldNotBeTheName"
                    if res['username'] + "_temp" in keys.keys():
                        f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                        try:
                            file_name = f.decrypt(res['f']).decode()
                            del keys[res['username'] + "_temp"]
                            with open(f"{username}_keys.json", 'w') as key_file:
                                key_file.write(json.dumps(keys))
                        except:
                            f = Fernet(base64.b64decode(keys[res['username'] + "_temp"].encode('utf-8')))
                            file_name = f.decrypt(res['f']).decode()
                    else:
                        f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                        file_name = f.decrypt(res['f']).decode()
                    dict_lock.release()
                    if not exists(username + "_files"): os.makedirs(username + "_files")
                    with open(username + "_files/" + file_name, "wb") as new_file:
                        encrypted_file = Message.recv(Client)
                        decrypted_file = f.decrypt(encrypted_file)
                        file = base64.b64decode(decrypted_file)
                        new_file.write(file)

                    if 'sender' in res.keys():
                        self.messages = res['username'].split("__")[1] +": " + res["sender"] + " sent file: " + file_name + "\n" + self.messages
                    else:
                        self.messages = res["username"] + " sent file: " + file_name + "\n" + self.messages

            except Exception as e:
                log_txt.write(str(e) + "\n--------\n")
                log_txt.write(traceback.format_exc())
                log_txt.flush()

class Chat(App):
    """Application running the textual interface.
    """
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, Client):
        """Concstructor of the application. Starts a receiving thread.

        :param Client: connection with the server
        :type Client: socket.socket
        """
        super().__init__()
        self.inbox = input_box()
        self.receiving_thread = threading.Thread(target=input_box.receive_messages, args=(self.inbox, Client))
        self.receiving_thread.start()
        # send_message("hello", input("receiver: "), Client)

    def compose(self) -> ComposeResult:
        """Renders the interface.

        :yield: Widgets to be displayed on the screen.
        :rtype: Iterator[ComposeResult]
        """
        yield Input(placeholder="Command", id="cmd")
        yield Input(placeholder="Enter the name of the receiver", id="recv")
        yield Input(placeholder="Message", id="msg")
        yield self.inbox
        yield Header(name = "FastChat", show_clock=True, )
        yield Footer()

    def on_input_submitted(self):
        """Sends messages/commands to the server based on the input received from the server.
        """
        inbox = self.query_one(input_box)
        msg = self.query_one("#msg", Input)
        recv = self.query_one("#recv", Input)
        cmd = self.query_one("#cmd", Input)

        try :

            if cmd.value[:3] == "del":
                if(recv.value == "" or cmd.value[4:] =="" ): return
                del_from_grp(recv.value, cmd.value[4:], Client)
                cmd.value = "g"

            elif cmd.value[:3] == "add":
                if(recv.value == "" or cmd.value[4:] ==""  ): return
                add_to_grp(recv.value, cmd.value[4:], Client)
                cmd.value = "g"

            elif cmd.value[:6] == "create":
                if(cmd.value[7:] =="" ): return
                log_txt.write("reached")
                log_txt.flush()
                make_grp(cmd.value[7:], Client)
                cmd.value = ""
                
            elif cmd.value[0] == "g":
                if(msg.value == "" or recv.value == ""): return

                grp_name = ""
                for grp in keys.keys():
                    if(grp.rfind("__") == -1): continue

                    if(grp.split("__", 1)[1] == recv.value):
                        grp_name =  grp
                        break
                if(grp_name == ""):
                    recv.value = ""
                    return 

                if cmd.value[2:] == "file":
                    send_file(msg.value, grp_name, Client)
                    log_txt.write("sent file\n")
                    log_txt.flush()
                else:
                    send_message(msg.value, grp_name, Client)
                
                inbox.messages = "sent to grp " + recv.value + ": " + msg.value + "\n" + inbox.messages
                msg.value = ""
                cmd.value = "g"

            elif cmd.value[:2] == "dm":

                if msg.value == "" or recv.value == "": 
                    return  

                if cmd.value[3:] == "file":
                    send_file(msg.value, recv.value, Client)
                else:
                    send_message(msg.value, recv.value, Client)
                
                inbox.messages = "sent to " + recv.value + ": " + msg.value + "\n" + inbox.messages
                msg.value = ""
                cmd.value = "dm"

        except Exception as e:
            log_txt.write(str(e) + "\n--------\n")
            log_txt.write(traceback.format_exc())
            log_txt.flush()
        # msg.value = ""

# app = Chat(Client)
time.sleep(1)

#----------------------------------------------Command line input handler--------------------------------------#

def input_handler(cmd:str, recv:str, msg:str):
    """Handles the input given from the command line interface. This interface can be used by passing in the `--cmd` flag in the command line.

    :param cmd: user command.
    :type cmd: str
    :param recv: receiver
    :type recv: str
    :param msg: message
    :type msg: str
    """
    try :

        if cmd[:3] == "del":
            if(recv == "" or cmd[4:] =="" ): return
            # t1 = str(time.time_ns())
            del_from_grp(recv, cmd[4:], Client)
            # t2 = str(time.time_ns())
            # msg_log_txt.write(cmd + ", " + recv + ", " + msg + ", " + str(t1) + ", " + str(t2) + "\n")
            # msg_log_txt.flush()

        elif cmd[:3] == "add":
            if(recv == "" or cmd[4:] ==""  ): return
            # t1 = str(time.time_ns())
            add_to_grp(recv, cmd[4:], Client)
            # t2 = str(time.time_ns())
            # log_txt.write(cmd + ", " + recv + ", " + msg + ", " + str(t1) + ", " + str(t2) + "\n")
            # log_txt.flush()

        elif cmd[:6] == "create":
            if(cmd[7:] =="" ): return

            # t1 = str(time.time_ns())
            make_grp(cmd[7:], Client)
            # t2 = str(time.time_ns())
            # msg_log_txt.write(cmd + ", " + recv + ", " + msg + ", " + str(t1) + ", " + str(t2)+ "\n")
            # msg_log_txt.flush()
            
        elif cmd[0] == "g":
            if(msg == "" or recv == ""): return

            grp_name = ""
            for grp in keys.keys():
                if(grp.rfind("__") == -1): continue

                if(grp.split("__", 1)[1] == recv):
                    grp_name =  grp
                    break
            if(grp_name == ""):
                recv = ""
                return 

            t = str(time.time_ns())
            if cmd[2:] == "file":
                send_file(msg, grp_name, Client)
                log_txt.write("sent file\n")
            else:
                send_message(msg, grp_name, Client)
            
            # t2 = str(time.time_ns())
            # msg_log_txt.write(cmd + ", " + recv + ", " + msg + ", " + str(t) + "\n")
            # msg_log_txt.flush()
            log_txt.flush()

            # inbox.messages = "sent to grp " + recv + ": " + msg + "\n" + inbox.messages
            print("sent to grp " + recv + ": " + msg )
            # send_message(msg, grp_name, Client)
            msg = ""
            cmd = "g"

        elif cmd[:2] == "dm":

            if msg == "" or recv == "": 
                return  

            t = str(time.time_ns())
            if cmd[3:] == "file":
                send_file(msg, recv, Client)
                msg_log_txt.write(f"df, {recv}, {msg}, {t}\n")
            else:
                send_message(msg, recv, Client)
                msg_log_txt.write(f"dm, {recv}, {msg}, {t}\n")
            msg_log_txt.flush()

            # inbox.messages = "sent to " + recv + ": " + msg + "\n" + inbox.messages
            print("sent to " + recv + ": " + msg)

    except Exception as e:
        log_txt.write(str(e) + "\n--------\n")
        log_txt.write(traceback.format_exc())
        log_txt.flush()

def receive_messages(Client: socket.socket) -> None:
    """Receives and prints messages from the server in the command line interface.

    :param Client: connection with the server.
    :type Client: socket.socket
    """
    while True:
        # res = Client.recv(2048)
        res = Message.recv(Client)
        if not res:
            break
        res = res.decode()
        log_txt.write(res + "\n")
        log_txt.flush()
        res = json.loads(res)
        try:
            if 'k' in res.keys():
                recvd_key = rsa.decrypt(base64.b64decode(res['k'].encode()), privkey).decode()
                
                dict_lock.acquire()
                if res['username'] in keys.keys():
                    if recvd_key > keys[res['username']]:
                        keys[res['username'] + "_temp"] = recvd_key
                    elif recvd_key < keys[res['username']]:
                        keys[res['username'] + "_temp"] = keys[res['username']]
                        keys[res['username']] = recvd_key
                else:
                    keys[res['username']] = recvd_key
                with open(f"{username}_keys.json", 'w') as key_file:
                    key_file.write(json.dumps(keys))
                dict_lock.release()
                # t = str(time.time_ns())
                # msg_log_txt.write("received key, " + res['username'] + ", " + str(t), + "\n")
                # msg_log_txt.flush()
                # print(keys[res['username']])
                # self.messages = "connected to user "+ res["username"] + "\n" + self.messages
                # print("connected to user "+ res["username"])

            elif 'km' in res.keys():
                # # f = Fernet(base64.b64decode(keys[res['username'].split('__')[0]].encode('utf-8')))
                # # decoded_key = f.decrypt(res['km']).decode()
                # decoded_key = ""
                # dict_lock.acquire()
                # if res['sender'] + "_temp" in keys.keys():
                #     f = Fernet(base64.b64decode(keys[res['sender']].encode('utf-8')))
                #     # f2 = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                #     try:
                #         decoded_key = f.decrypt(res['km']).decode()
                #         del keys[res['sender'] + "_temp"]
                #         with open(f"{username}_keys.json", 'w') as key_file:
                #             key_file.write(json.dumps(keys))
                #     except:
                #         f = Fernet(base64.b64decode(keys[res['sender'] + "_temp"].encode('utf-8')))
                #         decoded_key = f.decrypt(res['km']).decode()
                # else:
                #     f = Fernet(base64.b64decode(keys[res['sender']].encode('utf-8')))
                #     decoded_key = f.decrypt(res['km']).decode()

                # keys[res['username']] = decoded_key
                # with open(f"{username}_keys.json", 'w') as key_file:
                #     key_file.write(json.dumps(keys))
                    
                # dict_lock.release()
                # # t = str(time.time_ns())
                # # msg_log_txt.write("added to group, " + res['username'] + ", " + str(t) + "\n")
                # # msg_log_txt.flush()
                # # self.messages = "added to group "+ res["username"].split('__')[1]  + "\n" + self.messages
                # # print("added to group "+ res["username"].split('__')[1])
                # # print(decoded_msg)
                # # self.messages = res["username"] + " sent: " + decoded_key + "\n" + self.messages
                f = Fernet(base64.b64decode(keys[res['username'].split('__')[0]].encode('utf-8')))
                decoded_key = f.decrypt(res['km']).decode()
                keys[res['username']] = decoded_key
                with open(f"{username}_keys.json", 'w') as key_file:
                    key_file.write(json.dumps(keys))


            elif 'm' in res.keys():
                decoded_msg = ""
                dict_lock.acquire()
                if res['username'] + "_temp" in keys.keys():
                    f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    # f2 = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    try:
                        decoded_msg = f.decrypt(res['m']).decode()
                        del keys[res['username'] + "_temp"]
                        with open(f"{username}_keys.json", 'w') as key_file:
                            key_file.write(json.dumps(keys))
                    except:
                        f = Fernet(base64.b64decode(keys[res['username'] + "_temp"].encode('utf-8')))
                        decoded_msg = f.decrypt(res['m']).decode()
                else:
                    f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    decoded_msg = f.decrypt(res['m']).decode()
                dict_lock.release()

                # print(decoded_msg)
                if 'sender' in res.keys():
                    # self.messages = res['username'].split("__")[1] +": " + res["sender"] + " sent: " + decoded_msg + "\n" + self.messages
                    t = str(time.time_ns())
                    dis = res['username'].split("__")[1] +": " + res["sender"] + " sent: " + decoded_msg
                    # print(res['username'].split("__")[1] +": " + res["sender"] + " sent: " + decoded_msg)
                    # msg_log_txt.write(dis + ", " + str(t) + "\n")
                    # msg_log_txt.flush()
                    print(dis)
                else:
                    # self.messages = res["username"] + " sent: " + decoded_msg + "\n" + self.messages
                    # print(res["username"] + " sent: " + decoded_msg)
                    t = str(time.time_ns())
                    dis = res["username"] + " sent: " + decoded_msg
                    msg_log_txt.write( f"recvd, {res['username']}, {decoded_msg}, {t}\n")
                    msg_log_txt.flush()
                    print(dis)
            elif 'gd' in res.keys():
                # delete from group
                del keys[res['username']]
                with open(f"{username}_keys.json", 'w') as key_file:
                    key_file.write(json.dumps(keys))
                # print("removed from group " + res['username'])
                dis = "removed from group " + res['username']
                print(dis)
                # t = str(time.time_ns())
                # msg_log_txt.write(dis + ", " + str(t) + "\n")
                # msg_log_txt.flush()

            elif 'c' in res.keys():
                input_box.communicator_buffer = res['c'].encode()
                log_txt.write(res['c'] + "\n")
                log_txt.flush()
            elif 'f' in res.keys():
                # f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                dict_lock.acquire()
                f = None
                file_name = "thisShouldNotBeTheName"
                if res['username'] + "_temp" in keys.keys():
                    f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    # f2 = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    try:
                        file_name = f.decrypt(res['f']).decode()
                        del keys[res['username'] + "_temp"]
                        with open(f"{username}_keys.json", 'w') as key_file:
                            key_file.write(json.dumps(keys))
                    except:
                        f = Fernet(base64.b64decode(keys[res['username'] + "_temp"].encode('utf-8')))
                        file_name = f.decrypt(res['f']).decode()
                else:
                    f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    file_name = f.decrypt(res['f']).decode()
                dict_lock.release()
                # file_name = f.decrypt(res['f']).decode()
                if not exists(username + "_files"): os.makedirs(username + "_files")
                with open(username + "_files/" + file_name, "wb") as new_file:
                    encrypted_file = Message.recv(Client)
                    decrypted_file = f.decrypt(encrypted_file)
                    file = base64.b64decode(decrypted_file)
                    new_file.write(file)

                if 'sender' in res.keys():
                    # self.messages = res['username'].split("__")[1] +": " + res["sender"] + " sent file: " + file_name + "\n" + self.messages
                    # print(res['username'].split("__")[1] +": " + res["sender"] + " sent file: " + file_name)
                    dis = res['username'].split("__")[1] +": " + res["sender"] + " sent file: " + file_name
                    print(dis)
                    # t = str(time.time_ns())
                    # msg_log_txt.write(dis + ", " + str(t) + "\n")
                    # msg_log_txt.flush()
                else:
                    # self.messages = res["username"] + " sent file: " + file_name + "\n" + self.messages
                    # print(res["username"] + " sent file: " + file_name)
                    dis = res["username"] + " sent file: " + file_name
                    print(dis)
                    t = str(time.time_ns())
                    msg_log_txt.write(f"rf, {res['username']}, {file_name}, {t}\n")
                    msg_log_txt.flush()

        except Exception as e:
            log_txt.write(str(e) + "\n--------\n")
            log_txt.write(traceback.format_exc())
            log_txt.flush()


#--------------------------------------------------------------------------------------------------------------#
"""Decides which interface to run based on the flag given.
"""
if len(sys.argv) > 1 and sys.argv[1] == "--cmd":
    receiving_thread = threading.Thread(target=receive_messages, args=(Client, ))
    receiving_thread.start()
    instruction = ""
    while True:
        instruction = input()
        if instruction == "exit":
            break
        instruction = instruction.split(',') + ["", ""]
        instruction = [i.strip() for i in instruction]
        cmd, recv, msg = instruction[0], instruction[1], instruction[2]
        input_handler(cmd, recv, msg)
    Client.shutdown(socket.SHUT_RDWR)
    Client.close()
    log_txt.close()
    msg_log_txt.close()
else:
    app = Chat(Client)
    try:
        app.run()
    except Exception as e:
        log_txt.write(str(e) + "\n--------\n")
        log_txt.write(traceback.format_exc())
        log_txt.flush()
        Client.shutdown(socket.SHUT_RDWR)
        Client.close()
        msg_log_txt.close()

