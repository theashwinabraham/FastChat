import socket
import threading
import psycopg2
import json 
import end2end
import ports
import rsa
from cryptography.fernet import Fernet
import time
import base64
# imports for the UI
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Header, Footer
from textual.reactive import reactive

import traceback

# def message_sender(Client):
#     prompt = 'Enter the recipient name: '
#     while True:
#         reciever = input(prompt)
#         if(reciever == "NONE"):
#             break
#         message = input("Message: ")
#         Client.sendall(str.encode(wrap_message(reciever, message)))
#         # res = Client.recv(1024)
#         # print(res.decode('utf-8'))

# def message_reciever(Client):
#     prompt = 'Enter the recipient name: '
#     while True:
#         res = Client.recv(1024)
#         if not res:
#             break
#         #delete the old prompt and print the received message
#         # a = sys.stdin.read(1)
#         # print("a: ", a, flush=True)
#         print("\r", flush=True, end="")
#         sys.stdout.write("\033[K")
#         print("Received: ", res.decode('utf-8'))
#         print(prompt, end = "", flush=True)

#stores the keys for encryption
keys = {}

def wrap_message(reciever, message):
    return reciever+"\n"+message

def parse_message(message):
    l =  message.split("\n")
    return [l[0], l[1]]

def verify_with_server(username, password, server):
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
    assert(isinstance(server, socket.socket))
    #generating the rsa keys
    global pubkey
    global privkey
    global keys

    # send login id, password, and public key to server
    pubkey, privkey = rsa.newkeys(1024, poolsize=8)
    server = end2end.createComunicator(server, 100)
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
    assert(isinstance(server, socket.socket))
    choice = input("Press 0 for login and 1 for signup: ")
    if choice == "1":
        while True:
            username = input("Enter username: ")
            password = input("Enter password: ")
            res = add_to_server(username, password, server)
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

    if receiver in keys.keys():
        global fernet_key
        fernet_key = keys[receiver]
        fernet_key = base64.b64decode(fernet_key.encode())
    else:
        request = {"receiver": receiver, "action": 0}
        Client.sendall(json.dumps(request).encode())

        recv_pubkey = Client.recv(2048)
        if recv_pubkey.decode() == "None":
            return False
    
        recv_pubkey = rsa.PublicKey._load_pkcs1_pem(recv_pubkey)

        fernet_key = Fernet.generate_key()
        b64_fernet_key = base64.b64encode(fernet_key)
        keys[receiver] = b64_fernet_key.decode()
        
        # assert(fernet_key.decode().encode() == fernet_key)
        encrypted_key = base64.b64encode(rsa.encrypt(b64_fernet_key, recv_pubkey))
        # print("encrypted key: ", encrypted_key)
        Client.sendall(encrypted_key)

        with open(f"{username}_keys.json", 'w') as key_file:
            key_file.write(json.dumps(keys))

    f = Fernet(fernet_key)
    encoded_msg = f.encrypt(msg.encode('utf-8'))
    msg_dict = {"receiver": receiver, "message": encoded_msg.decode('utf-8'), "action": 1}
    Client.sendall(json.dumps(msg_dict).encode('utf-8'))
    return True

def add_to_grp(grp_name, new_user, Client: socket.socket) -> bool:

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
        Client.sendall(json.dumps(request).encode())

        recv_pubkey = Client.recv(2048)
        if recv_pubkey.decode() == "None":
            return False
    
        recv_pubkey = rsa.PublicKey._load_pkcs1_pem(recv_pubkey)

        user_fernet_key = Fernet.generate_key()
        b64_fernet_key = base64.b64encode(user_fernet_key)
        keys[new_user] = b64_fernet_key.decode()
        
        # assert(fernet_key.decode().encode() == fernet_key)
        encrypted_key = base64.b64encode(rsa.encrypt(b64_fernet_key, recv_pubkey))
        # print("encrypted key: ", encrypted_key)
        Client.sendall(encrypted_key)

        with open(f"{username}_keys.json", 'w') as key_file:
            key_file.write(json.dumps(keys))
    
    user_f = Fernet(user_fernet_key)

    encrypted_key = user_f.encrypt(grp_fernet_key.encode())

    msg_dict = {"grp_name": grp_name, "username": new_user, "key": encrypted_key.decode('utf-8'), "action": 4}
    msg_dict = json.dumps(msg_dict).encode()
    Client.sendall(msg_dict)

    res = Client.recv(2048)

    if (res.decode() == "1"):
        return True
    else:
        return False

def del_from_grp(grp_name, del_user, Client: socket.socket) -> bool:
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
    Client.sendall(msg_dict)
    
    res = Client.recv(2048)
    if (res.decode() == "1"):
        return True
    else:
        return False


def make_grp(grp_name, Client: socket.socket) -> bool:

    # groups in the format username__groupname stored in keys

    log_txt.write("reached")
    log_txt.flush()

    grp_name = username + "__" + grp_name
    if grp_name in keys.keys():
        return False
    
    msg_dict = {'action' : 5, 'grp_name': grp_name}
    msg_dict = json.dumps(msg_dict).encode()

    log_txt.write("reached")
    log_txt.flush()

    Client.sendall(msg_dict)

    log_txt.write("reached")
    log_txt.flush()

    res = Client.recv(2048)

    log_txt.write("reached" + res.decode())
    log_txt.flush()

    if (res.decode() == "1"):
        log_txt.write("reached")
        log_txt.flush()    
        grp_fernet_key = Fernet.generate_key()
        b64_grp_fernet_key = base64.b64encode(grp_fernet_key)
        keys[grp_name] = b64_grp_fernet_key.decode()

        log_txt.write("reached")
        log_txt.flush()    
        with open(f"{username}_keys.json", 'w') as key_file:
            key_file.write(json.dumps(keys))
        return True
    else:
        return False



Client = socket.socket()
host = '127.0.0.1'
# port = 9000
# print('Waiting for connection response')
try:
    port = ports.auth_server_port
    Client.connect((host, port))
except socket.error as e:
    print(f'Could not connect to the auth_server: {e}')
    exit(-1)

res = authenticate(Client)
data, username, password = res
if not data:
    exit(-1)

log_txt = open(f'log_{username}.txt', 'w')
host, port, otp = (data['host'], data['port'], data['otp'])
Client.close()
#connect to the new server
time.sleep(1)
Client = socket.socket()
try:
    Client.connect((host, port))
except socket.error as e:
    print(f"Can't connect to server: {e}")
    exit(-1)
print(username, password)
# print("Please enter your name: ", end="", flush=True)
# name = input()
Client.sendall(bytes(username, "utf-8"))
print(host, port, otp)
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
    messages = reactive("")
    msg = ""
    #renders the text on the screen
    def render(self) -> str:
        return self.messages
    #receives messages from the server
    def receive_messages(self, Client: socket.socket) -> None:
        while True:
            res = Client.recv(2048)
            if not res:
                break
            res = res.decode()
            log_txt.write(res + "\n")
            log_txt.flush()
            res = json.loads(res)
            try:
                if 'k' in res.keys():
                    keys[res['username']] = rsa.decrypt(base64.b64decode(res['k'].encode()), privkey).decode()
                    # print(keys[res['username']])
                    self.messages = "connected to user "+ res["username"] + "\n" + self.messages
                    with open(f"{username}_keys.json", 'w') as key_file:
                        key_file.write(json.dumps(keys))

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
                    f = Fernet(base64.b64decode(keys[res['username']].encode('utf-8')))
                    decoded_msg = f.decrypt(res['m']).decode()
                    # print(decoded_msg)
                    self.messages = res["username"] + " sent: " + decoded_msg + "\n" + self.messages
                    
                elif 'gd' in res.keys():
                    del keys[res['username']]
                    with open(f"{username}_keys.json", 'w') as key_file:
                        key_file.write(json.dumps(keys))
            except Exception as e:
                log_txt.write(str(e) + "\n--------\n")
                log_txt.write(traceback.format_exc())
                log_txt.flush()

class Chat(App):

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, Client):
        super().__init__()
        self.inbox = input_box()
        self.receiving_thread = threading.Thread(target=input_box.receive_messages, args=(self.inbox, Client))
        self.receiving_thread.start()
        # send_message("hello", input("receiver: "), Client)

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Command", id="cmd")
        yield Input(placeholder="Enter the name of the receiver", id="recv")
        yield Input(placeholder="Message", id="msg")
        yield self.inbox
        yield Header(name = "FastChat", show_clock=True, )
        yield Footer()

    def on_input_submitted(self):
        inbox = self.query_one(input_box)
        msg = self.query_one("#msg", Input)
        recv = self.query_one("#recv", Input)
        cmd = self.query_one("#cmd", Input)

        try :

            if cmd.value[:3] == "del":
                if(recv.value == "" or cmd.value[4:] =="" ): return
                del_from_grp(recv.value, cmd.value[4:], Client)
                cmd.value = ""

            elif cmd.value[:3] == "add":
                if(recv.value == "" or cmd.value[4:] ==""  ): return
                add_to_grp(recv.value, cmd.value[4:], Client)
                cmd.value = ""

            elif cmd.value[:6] == "create":
                if(cmd.value[7:] =="" ): return
                log_txt.write("reached")
                log_txt.flush()
                make_grp(cmd.value[7:], Client)
                cmd.value = ""
                
            elif cmd.value == "g":
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
                
                inbox.messages = "sent to grp " + recv.value + ": " + msg.value + "\n" + inbox.messages
                send_message(msg.value, grp_name, Client)
                recv.value = ""

            elif cmd.value[:2] == "dm":

                if msg.value == "" or recv.value == "": 
                    return  

                inbox.messages = "sent to " + recv.value + ": " + msg.value + "\n" + inbox.messages

                send_message(msg.value, recv.value, Client)
                msg.value = ""
                # Client.sendall(str.encode(wrap_message(recv.value, msg.value)))
        except Exception as e:
            log_txt.write(str(e) + "\n--------\n")
            log_txt.write(traceback.format_exc())
            log_txt.flush()
        # msg.value = ""

app = Chat(Client)
time.sleep(1)
try:
    app.run()
except Exception as e:
    log_txt.write(str(e) + "\n--------\n")
    log_txt.write(traceback.format_exc())
    log_txt.flush()