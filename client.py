import socket
import threading
import psycopg2
import json 
import end2end
import ports
import sys
# imports for the UI
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Header, Footer
from textual.reactive import reactive

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
def wrap_message(reciever, message):
    return reciever+"\n"+message

def parse_message(message):
    l =  message.split("\n")
    return [l[0], l[1]]

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
                return (res, username, password)            
    else:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        return (verify_with_server(username, password, server), username, password)

Client = socket.socket()
host = '127.0.0.1'
port = 9000
# print('Waiting for connection response')
try:
    port = ports.auth_server_port
    Client.connect((host, port))
except socket.error as e:
    print(str(e))

res = authenticate(Client)
data, username, password = res
if not data:
    exit(-1)
host, port, otp = (data['host'], data['port'], data['otp'])
Client.close()
#connect to the new server
Client = socket.socket()
try:
    Client.connect((host, port))
except socket.error as e:
    print(e)
print(username, password)
# print("Please enter your name: ", end="", flush=True)
# name = input()
Client.sendall(bytes(username, "utf-8"))
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
            res = Client.recv(1024)
            if not res:
                break
            res = parse_message(res.decode())
            self.messages = res[0] + " sent: " + res[1] + "\n" + self.messages

class Chat(App):

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, Client):
        super().__init__()
        self.inbox = input_box()
        self.receiving_thread = threading.Thread(target=input_box.receive_messages, args=(self.inbox, Client))
        self.receiving_thread.start()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter the name of the receiver", id="recv")
        yield Input(placeholder="Message", id="msg")
        yield self.inbox
        yield Header(name = "FastChat", show_clock=True)
        yield Footer()

    def on_input_submitted(self):
        inbox = self.query_one(input_box)
        msg = self.query_one("#msg", Input)
        recv = self.query_one("#recv", Input)
        if msg.value == "": 
            return  
        inbox.messages = "sent: " + msg.value + "\n" + inbox.messages
        Client.sendall(str.encode(wrap_message(recv.value, msg.value)))
        msg.value = ""

app = Chat(Client)
app.run()