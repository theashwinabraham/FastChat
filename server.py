import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 10000)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

sock.listen(1)

while(True):
    print('Waiting')
    connection, client_address = sock.accept()
    try:
        print('connection from ', client_address)
        while True:
            data = connection.recv(16)
            print('recieved {!r}'.format(data))
            if data:
                print('sending data back to the client')
                connection.sendall(data)
            else:
                print('no data from ', client_address)
                break
    except(Exception):
        print("hello", Exception)
    finally:
        connection.close()