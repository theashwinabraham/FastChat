import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 10000)
print('connecting from {} to port {}'.format(*server_address))
sock.connect(server_address)

try:
    message = b'This is the message. It will be repeated.'
    print('sending {!r}'.format(message))
    sock.sendall(message)

finally:
    print('closing socket')
    sock.close()