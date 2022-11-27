from pwn import *
import time
import threading
import os
from os.path import exists

import random

NUM_CLIENTS = 20
IMG_FILE = "jv_bokassa.png"
MSG_SPEED = 5
NUM_ITERATIONS = 5
USER_PREFIX = "user"
NUM_SERVERS = 2

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
        time.sleep(5)
        self.repetitive_msg(1, 1)
        time.sleep(5)

        for i in range(NUM_ITERATIONS):
            self.repetitive_msg(i+2, 20.0/MSG_SPEED)
        # for i in range(5):
        #     self.img_msg(i+2, 10)

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
        for i in range(NUM_CLIENTS*2* (NUM_ITERATIONS+2) ):
            try:
                self.log_file.write(self.ps.recvuntil(b"d", timeout=10) + b"d")
                # self.log_file.flush()
            except:
                pass
        self.ps.sendline(b'exit')
        if self.ps.poll(block = True):
            self.ps.close()

if not exists("log"): os.makedirs("log")
os.system("bash cleaner.sh >/dev/null")

auth_ps = process(argv=["./auth_server.py", ])
time.sleep(2)
servers_ps = [process(argv=["./server.py", str(1+i), str(9001+i)]) for i in range(NUM_SERVERS)]
time.sleep(2)

clients1 = [Client(f"{USER_PREFIX}{i}") for i in range(0, int(NUM_CLIENTS/2))]
print("LMAO")
threads1 = [threading.Thread(target=Client.create_process, args=(client,)) for client in clients1]
for thread in threads1:
    thread.start()

print("LMAO1")
time.sleep(5)
print("LMAO2")

clients2 = [Client(f"{USER_PREFIX}{i}") for i in range(int(NUM_CLIENTS/2), NUM_CLIENTS)]
threads2 = [threading.Thread(target=Client.create_process, args=(client,)) for client in clients2]
for thread in threads2:
    thread.start()


# for thread in threads[int(len(threads)/2):]:
#     thread.start()

closing_threads = [threading.Thread(target=Client.close, args=(client,)) for client in clients1+clients2]
for thread in closing_threads:
    thread.start()

for thread in threads1+threads2:
    thread.join()

for thread in closing_threads:
    thread.join()

os.system(f"python3.8 analysis.py {NUM_CLIENTS}  {USER_PREFIX}")
