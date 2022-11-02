import socket
from threading import *
import psycopg2
import json 

def message_sender(ClientMultiSocket):
    prompt = 'Enter the recipient number(enter NONE if you want to stop messaging):'
    while True:
        reciever = input(prompt)
        if(reciever == "NONE"):
            break
        message = input("Message: ")
        ClientMultiSocket.sendall(str.encode(wrap_message(reciever, message)))
        # res = ClientMultiSocket.recv(1024)
        # print(res.decode('utf-8'))

def message_reciever(ClientMultiSocket):
    prompt = 'Enter the recipient number(enter NONE if you want to stop messaging):'
    while True:
        res = ClientMultiSocket.recv(1024)
        if not res:
            break
        print("\nReceived: ", res.decode('utf-8'))
        print(prompt, end = "", flush=True)

def wrap_message(reciever, message):
    return reciever+"\n"+message

def verify_with_server(username, passsword, server):
    assert(isinstance(server, socket.socket))
    auth_data = {"username": username, "password": passsword}
    auth_data = json.dumps(auth_data)
    server.send(bytes(auth_data, encoding='utf-8'))
    data = server.recv(1024)
    print(data)

def add_to_server(uname, upwd):
    pass

def make_user_sql(uname, upwd):
    pass

def connect_to_sql(params):
    conn = psycopg2.connect(**params)
    pass

def authenticate(server):
    assert(isinstance(server, socket.socket))
    choice = input("Press 0 for login and 1 for signup: ")
    if choice == "1":
        username = input("Enter username: ")
        password = input("Enter password: ")
        add_to_server(username, password)
        make_user_sql(username, password)
        pass
    else:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        verify_with_server(username, password, server)
        pass

ClientMultiSocket = socket.socket()
host = '127.0.0.1'
port = 9000
print('Waiting for connection response')
try:
    port = 10001
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))
authenticate(ClientMultiSocket)
# res = ClientMultiSocket.recv(1024)

# receiving_thread = Thread(target=message_reciever, args=(ClientMultiSocket, ))
# sending_thread = Thread(target=message_sender, args=(ClientMultiSocket, ))
# receiving_thread.start()
# sending_thread.start()

# ClientMultiSocket.close()

