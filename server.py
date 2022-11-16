import socket
import threading
import ports
import sys

if len(sys.argv) == 1:
    print("Usage: python3 server.py <server_id>")
    exit(-1)

from client_handler import *

ServerSideSocket = socket.socket()
host = ports.server_host
port = ports.server_port
ThreadCount = 0
auth_host = ports.auth_server_host
auth_port = ports.auth_server_port

try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
ServerSideSocket.listen(1)
authInterface = threading.Thread(target=client_handler.authServerInterface, args=(auth_host, auth_port))
authInterface.start()
message_distributor = threading.Thread(target = client_handler.distribute_messages)
message_distributor.start()
try:
    while True:
        #we cannot have a recv statement inside this loop
        #else the server stops accepting connections till the previous connection receives data 
        Client, address = ServerSideSocket.accept()
        t = threading.Thread(target = client_handler.getClientName, args = (Client, ))
        t.start()
        # name = bytes.decode(Client.recv(1024))
        # print('Connected to: ' + address[0] + ':' + str(address[1]))
        # obj = client_handler(name)
        # t = Thread(target = client_handler.multi_threaded_client, args = (obj, Client))
        # t.start()
        # t1 = Thread(target = client_handler.send_messages, args = (obj, ))
        # t1.start()
        # client_handler.active_threads[name] = (obj, t, t1, Client)
        # print(client_handler.active_threads)
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))
finally:
    ServerSideSocket.close()