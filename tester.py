from pwn import *
import time
import threading
import os
from os.path import exists

import random

NUM_CLIENTS = 2
IMG_FILE = "jv_bokassa.png"

if not exists("log"): os.makedirs("log")

for i in range(7):
    os.system(f"cp {IMG_FILE} {i}_{IMG_FILE}")

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

        self.repetitive_msg(0, 1)
        time.sleep(3)
        self.repetitive_msg(1, 1)
        time.sleep(5)

        for i in range(5):
            self.repetitive_msg(i+2, 2)
        # for i in range(5):
        #     self.img_msg(i+2, 10)
        

        # self.img_msg()

        # self.img_msg()

        # for user in Client.users:
        #     self.ps.sendline(f'dm, {user}, helloworld'.encode())
            # time.sleep(1)

        # for i in range(NUM_CLIENTS*2 ):
        #     self.log_file.write(self.ps.recvuntil(b"\n", 1) + b"\n")
        #     self.log_file.flush()
        # self.ps.sendline(b'exit')
        # time.sleep(20)

    def repetitive_msg(self, i, t):
        for user in Client.users:
            self.ps.sendline(f'dm, {user}, helloworld{i}'.encode())
            time.sleep(random.randint(0,10)/100.0*t)
        
    def img_msg(self, i, t):
        for user in Client.users:
            x = random.randint(1, 10)
            if x == 1:
                self.ps.sendline(f"dm file, {user}, {i}_{IMG_FILE}".encode())
            else:
                self.ps.sendline(f'dm, {user}, helloworld{i}'.encode())
            time.sleep(random.randint(0,10)/100.0*t)

    def close(self):
        # time.sleep(2)
        for i in range(NUM_CLIENTS*2* (10+2) ):
            try:
                self.log_file.write(self.ps.recvuntil(b"d", 5) + b"d")
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

