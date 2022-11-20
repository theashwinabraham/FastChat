import json
import constants
import random


def valid_user(cursor, auth_data):
    cursor.execute(f"SELECT * FROM AUTH_DATA WHERE USERNAME = '{auth_data['username']}'")
    data = cursor.fetchall()
    return len(data) > 0 and auth_data['password'] == data[0][1]

def add_user(auth_cursor, msg_cursor, auth_data):
    if len(auth_data['username'] == 0 or len(auth_data['password']) == 0):
        return False
    try:
        auth_cursor.execute(f"INSERT INTO AUTH_DATA (USERNAME, PASSWORD) VALUES ('{auth_data['username']}', '{auth_data['password']}')")
    except:
        return False

    msg_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {auth_data['username']}(
            timestamp TEXT PRIMARY KEY,
            message TEXT,
            username TEXT
        );""")
    
    return True



class LoadBalancer:
    Servers = []

    @classmethod
    def getHostAndPort(cls, username):
        # add code to distribute the client load optimally among servers
        host = constants.server_host
        port = constants.server_port
        otp = random.randint(10000, 99999)
        # print(cls.Servers)
        cls.Servers[0][0].send(bytes(json.dumps({'username':username, 'otp':otp}), "utf-8"))
        return {'host': host, 'port':port, 'otp': otp}

    @classmethod
    def addServer(cls, Client, id):
        cls.Servers.append((Client, id))

def interact(Client, sql_auth_conn, sql_auth_cur, sql_msg_conn, sql_msg_cur):
    while True:
        auth_data = Client.recv()
        # if not auth_data:
        #     return False
        assert(auth_data)
        auth_data = json.loads(auth_data.decode("utf-8"))
        if 'server_key' in auth_data.keys() and auth_data['server_key'] == constants.server_key: # Response from server
            print(f"Server { auth_data['id'] } connected")
            LoadBalancer.addServer(Client, auth_data['id'])
            break
        else: # Response from Client
            send_to_cl = bytes(json.dumps(LoadBalancer.getHostAndPort(auth_data['username'])), encoding='utf-8')
            if auth_data['action'] == 0:
                if not valid_user(sql_auth_cur, auth_data):
                    send_to_cl = b"{}"
            else:
                if not add_user(sql_auth_cur, sql_msg_cur, auth_data):
                    send_to_cl = b"{}"
            Client.send(send_to_cl)
            sql_auth_conn.commit()
            sql_msg_conn.commit()
            break
