import socket
import threading
import psycopg2
import json 
import end2end
import ports
import sys
#imports for the UI
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Input
from textual.reactive import reactive

def message_sender(Client):
    prompt = 'Enter the recipient name: '
    while True:
        reciever = input(prompt)
        if(reciever == "NONE"):
            break
        message = input("Message: ")
        Client.sendall(str.encode(wrap_message(reciever, message)))
        # res = Client.recv(1024)
        # print(res.decode('utf-8'))

def message_reciever(Client):
    prompt = 'Enter the recipient name: '
    while True:
        res = Client.recv(1024)
        if not res:
            break
        #delete the old prompt and print the received message
        # a = sys.stdin.read(1)
        # print("a: ", a, flush=True)
        print("\r", flush=True, end="")
        sys.stdout.write("\033[K")
        print("Received: ", res.decode('utf-8'))
        print(prompt, end = "", flush=True)

def wrap_message(reciever, message):
    return reciever+"\n"+message

def verify_with_server(username, password, server):
    assert(isinstance(server, socket.socket))
    server = end2end.createComunicator(server, 100)
    auth_data = {"username": username, "password": password, 'action': 0}
    auth_data = json.dumps(auth_data)
    server.send(bytes(auth_data, encoding='utf-8'))
    data = server.recv()
    data = json.loads(data)
    if(data == {}):
        print("authentication failed")
        return False
    else:
        return data

def add_to_server(username, password, server):
    assert(isinstance(server, socket.socket))
    server = end2end.createComunicator(server, 100)
    auth_data = {"username": username, "password": password, 'action':1}
    auth_data = json.dumps(auth_data)
    server.send(bytes(auth_data, encoding='utf-8'))
    data = server.recv()
    data = json.loads(data)
    if(data == {}):
        return False
    else:
        return data

def make_user_sql(uname, upwd):
    pass

def connect_to_sql(params):
    conn = psycopg2.connect(**params)
    pass

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
                return res            
    else:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        return verify_with_server(username, password, server)

Client = socket.socket()
host = '127.0.0.1'
port = 9000
# print('Waiting for connection response')
try:
    port = ports.auth_server_port
    Client.connect((host, port))
except socket.error as e:
    print(str(e))

data = authenticate(Client)
if not data:
    exit(-1)
host, port = (data['host'], data['port'])
Client.close()
#connect to the new server
Client = socket.socket()
try:
    Client.connect((host, port))
except socket.error as e:
    print(e)
print("Please enter your name: ", end="", flush=True)
name = input()
Client.sendall(bytes(name, "utf-8"))
Client.recv(1024)
# receiving_thread = threading.Thread(target=message_reciever, args=(Client, ))
# receiving_thread.start()
#..........................................................#
class input_box(Widget):
    messages = reactive("")
    msg = ""
    #renders the text on the screen
    def render(self) -> str:
        return self.messages
    #receives messages from the server
    def receive_messages(self, Client: socket.socket) -> None:
        while True:
            res = Client.recv(1024)
            if not res:
                break
            res = res.decode()
            self.messages = "received: " + res + "\n" + self.messages

class Chat(App):

    def __init__(self, Client):
        super().__init__()
        self.inbox = input_box()
        self.receiving_thread = threading.Thread(target=input_box.receive_messages, args=(self.inbox, Client))
        self.receiving_thread.start()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter the name of the receiver", id="recv")
        yield Input(placeholder="Message", id="msg")
        yield input_box()

    def on_input_submitted(self):
        inbox = self.query_one(input_box)
        msg = self.query_one("#msg", Input)
        recv = self.query_one("#recv", Input)
        inbox.messages = "sent: " + msg.value + "\n" + inbox.messages
        Client.sendall(str.encode(wrap_message(recv.value, msg.value)))
        msg.value = ""

app = Chat(Client)
app.run()
#..........................................................#
# receiving_thread = threading.Thread(target=message_reciever, args=(Client, ))
# sending_thread = threading.Thread(target=message_sender, args=(Client, ))
# receiving_thread.start()
# sending_thread.start()
# #need to join. Do this step, else the main thread closes the connection while the other threads are using it
# sending_thread.join()
# receiving_thread.join()
# Client.close()