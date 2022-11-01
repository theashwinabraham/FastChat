import socket
from threading import *
# from typing import Tuple
from client_handler import *

ServerSideSocket = socket.socket()
host = '127.0.0.1'
port = 9000
ThreadCount = 0

try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
ServerSideSocket.listen(1)

message_distributor = Thread(target = client_handler.send_messages)
message_distributor.start()
while True:
    Client, address = ServerSideSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    obj = client_handler()
    t = Thread(target = client_handler.multi_threaded_client, args = (obj, Client))
    t.start()
    t1 = Thread(target = client_handler.display_messages, args = (obj, ))
    t1.start()
    client_handler.active_threads.append([obj, t, t1, Client])
    # print(client_handler.active_threads)
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSideSocket.close()