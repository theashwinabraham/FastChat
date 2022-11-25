from pwn import *
import time
import threading
import os
from os.path import exists


NUM_CLIENTS = 8

if not exists("log"): os.makedirs("log")

class Client:
    # password = "pwd"

    users = []
    def __init__(self, username):
        self.ps = None
        self.username = username
        self.ps = process(argv=['./client.py', '--cmd'])
        self.ps.sendline(b'1')
        self.ps.sendline(self.username.encode())
        self.ps.sendline(self.username.encode())
        self.ps.recvuntil(b'word: ')
        Client.users.append(username)
        self.log_file = open("log/" + username+"_log.txt", "wb")
        
    def create_process(self)->None:


        for user in Client.users:
            self.ps.sendline(f'dm, {user}, helloworld'.encode())

        # for i in range(NUM_CLIENTS*2 ):
        #     self.log_file.write(self.ps.recvuntil(b"\n", 1) + b"\n")
        #     self.log_file.flush()
        # self.ps.sendline(b'exit')
        # time.sleep(20)
    def close(self):
        # time.sleep(2)
        for i in range(NUM_CLIENTS*2 ):
            try:
                self.log_file.write(self.ps.recvuntil(b"d", 2) + b"d")
                self.log_file.flush()
            except:
                pass
        self.ps.sendline(b'exit')
        if self.ps.poll(block = True):
            self.ps.close()

clients = [Client(f"user{i}") for i in range(NUM_CLIENTS)]

threads = [threading.Thread(target=Client.create_process, args=(client,)) for client in clients]
closing_threads = [threading.Thread(target=Client.close, args=(client,)) for client in clients]
for thread in threads:
    thread.start()

# time.sleep(10)

for thread in closing_threads:
    thread.start()

for thread in threads:
    thread.join()

# for c in clients:
#     c.ps.sendline(b'exit')
#     # c.log_file.write(c.ps.recv())
#     # c.log_file.flush()

for thread in closing_threads:
    thread.join()
