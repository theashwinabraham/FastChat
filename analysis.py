import time
import os
import sys
from matplotlib import pyplot as plt
import numpy as np

# dm, user110, helloworld, 1669380239478471140
# recvd, user110, helloworld, 1669380239478471140

NUM_CLIENTS = int(sys.argv[1])
USER_PREFIX = sys.argv[2]
msgs = ["helloworld1", "helloworld2", "helloworld3", "helloworld4",]

sent = [[{} for _ in range( NUM_CLIENTS)] for _ in range(NUM_CLIENTS)] #sent[i][j]->time when i sent to j
recvd = [[{} for _ in range(NUM_CLIENTS)] for _ in range(NUM_CLIENTS)] #recvd[i][j]->time when j received from i

for i in range(NUM_CLIENTS):
    with open(f"msg_log/log_{USER_PREFIX}{i}.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            L = [l.strip() for l in line.split(",")]
            # print(sent)
            if(L[0] == "dm"):
                j = int(L[1][len(USER_PREFIX):])
                sent[i][j][L[2]] = int(L[3])
            elif(L[0] == "recvd"):
                j = int(L[1][len(USER_PREFIX):])
                recvd[j][i][L[2]] = int(L[3])

# print(sent)
# print(recvd)
# print("----------------------------------")

for msg in msgs:
    times = []
    for i in range(NUM_CLIENTS):
        for j in range(NUM_CLIENTS):
            # print(i, j, sent[i][j].keys(), recvd[i][j].keys())
            times.append((recvd[i][j][msg] - sent[i][j][msg])*(10**-6))
    # print(times)
    times = np.array(times)
    print(np.average(times))
    plt.hist(times)
    plt.show()