import socket
from threading import *
import psycopg2

groupServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1'
port = 9002

try:
    groupServer.bind((host, port))
except Exception as e:
    print(e)
    socket.close()
    exit(-1)

groupServer.listen(1)

sql_conn = psycopg2.connect(database="GROUPS", user="ananth", password="ananth", host = "127.0.0.1", port = 5432)
sql_cur = sql_conn.cursor()

#create a table for each group