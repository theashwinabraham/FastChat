import time
import os
import sys
from matplotlib import pyplot as plt
import numpy as np

# dm, user110, helloworld, 1669380239478471140
# recvd, user110, helloworld, 1669380239478471140

NUM_CLIENTS = int(sys.argv[1])
USER_PREFIX = sys.argv[2]

sent = [[{} for _ in range( NUM_CLIENTS)] for _ in range(NUM_CLIENTS)] #sent[i][j]->time when i sent to j
recvd = [[{} for _ in range(NUM_CLIENTS)] for _ in range(NUM_CLIENTS)] #recvd[i][j]->time when j received from i

sent_f = [[{} for _ in range( NUM_CLIENTS)] for _ in range(NUM_CLIENTS)]
recv_f = [[{} for _ in range( NUM_CLIENTS)] for _ in range(NUM_CLIENTS)]

dm_times = []
df_times = []
recv_times = []
rf_times = []

for i in range(NUM_CLIENTS):
    with open(f"msg_log/log_{USER_PREFIX}{i}.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            L = [l.strip() for l in line.split(",")]
            # print(sent)
            j = int(L[1][len(USER_PREFIX):])
            if(L[0] == "dm"):
                sent[i][j][L[2]] = int(L[3])
                dm_times.append(int(L[3]))
            elif(L[0] == "recvd"):
                recvd[j][i][L[2]] = int(L[3])
                recv_times.append(int(L[3]))
            elif(L[0]== "rf"):
                recv_f[j][i][L[2]] = int(L[3])
                df_times.append(int(L[3]))
            elif(L[0] == "df"):
                sent_f[i][j][L[2]] = int(L[3])
                rf_times.append(int(L[3]))

# print(sent)
# print(recvd)
# print("----------------------------------")

times = []
# times_f = []
for id in range(2,10):
    for i in range(NUM_CLIENTS):
        for j in range(NUM_CLIENTS):
            # print(i, j, sent[i][j].keys(), recvd[i][j].keys())
            if f"helloworld{id}" in recvd[i][j].keys():
                times.append((recvd[i][j][f"helloworld{id}"] - sent[i][j][f"helloworld{id}"])*(10**-6))
            elif f"{id}_jv_bokassa.png" in recv_f[i][j].keys():
                times.append((recv_f[i][j][f"{id}_jv_bokassa.png"] - sent_f[i][j][f"{id}_jv_bokassa.png"])*(10**-6))

    # print(times)
times = np.array(times)
# times_f = np.array(times_f)
print("avg latency: ", np.average(times), "ms")
plt.hist(times)
# plt.show()
plt.savefig("report/test1/test3.png")

#calculating the throughput
dm_times.sort()
df_times.sort()
recv_times.sort()
rf_times.sort()

inp_tp = [[], []]
out_tp = [[], []]
for i in range(0, len(dm_times)-100, 100):
    inp_tp[0].append((10**11)/(dm_times[i+100] - dm_times[i]))
for i in range(0, len(recv_times)-100, 100):
    out_tp[0].append((10**11)/(recv_times[i+100] - recv_times[i]))

for i in range(0, len(df_times)-50, 50):
    inp_tp[1].append(0.5*(10**11)/(df_times[i+50] - df_times[i]))
for i in range(0, len(rf_times)-50, 50):
    out_tp[1].append(0.5*(10**11)/(rf_times[i+50] - rf_times[i]))

# inp_tp = np.array(inp_tp)
# out_tp = np.array(out_tp)
# plt.hist(inp_tp)
# plt.show()
# plt.hist(out_tp)
# plt.show()

print("inp_tp: ", np.average(np.array(inp_tp[0])), "msgs/second", np.average(np.array(inp_tp[1])), "imgs/second")
print("out_tp: ", np.average(np.array(out_tp[0])), "msgs/second", np.average(np.array(out_tp[1])), "imgs/second")

