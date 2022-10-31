import socket

def wrap_message(reciever, message):
    return reciever+"\n"+message

ClientMultiSocket = socket.socket()
host = '127.0.0.1'
port = 9001
print('Waiting for connection response')
try:
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))
res = ClientMultiSocket.recv(1024)
while True:
    reciever = input('Enter the recipient number(enter NONE if you want to stop messaging):')
    if(reciever == "NONE"):
        break
    message = input("Message: ")
    ClientMultiSocket.send(str.encode(wrap_message(reciever, message)))
    res = ClientMultiSocket.recv(1024)
    print(res.decode('utf-8'))
ClientMultiSocket.close()