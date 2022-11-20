import psycopg2
import socket
import end2end
import auth_client_handler
import constants
import selectors

host = constants.auth_server_host
port = constants.auth_server_port

# connect to psycopg2
sql_auth_conn = psycopg2.connect(database=constants.authdb, user=constants.usr, password=constants.pwd, host=constants.localhost, port = constants.default_port)
sql_auth_cur = sql_auth_conn.cursor()
# create a table of usernames and passwords
sql_auth_cur.execute('''
    CREATE TABLE IF NOT EXISTS AUTH_DATA(
        USERNAME TEXT PRIMARY KEY,
        PASSWORD TEXT
        );
''')
sql_auth_conn.commit()

sql_msg_conn = psycopg2.connect(database=constants.msg_storage, user=constants.usr, password=constants.pwd, host=constants.localhost, port = constants.default_port)
sql_msg_cur = sql_msg_conn.cursor()

with socket.socket() as auth_server:
    auth_server.bind((host, port))
    auth_server.listen(constants.auth_server_backlog)
#    auth_server.setblocking(False)
    with selectors.DefaultSelector() as selector:
        def accept(auth_server: socket.socket, _):
            Client, _ = auth_server.accept()
            print(f'Connected to {Client}')
#            Client.setblocking(False)
            Client = end2end.createComunicator(Client, 100)
            selector.register(Client, selectors.EVENT_READ, read)

        def read(Client, _):
            auth_client_handler.interact(Client, sql_auth_conn, sql_auth_cur, sql_msg_conn, sql_msg_cur)
            print(f'Connection to {Client} ended')

        selector.register(auth_server, selectors.EVENT_READ, accept)
        while True:
            # Client, _ = auth_server.accept() # Blocking (waits for input)
            # print(f'Connected to {Client}')
            # Client = end2end.createComunicator(Client, 100)
            # auth_client_handler.interact(Client, sql_auth_conn, sql_auth_cur, sql_msg_conn, sql_msg_cur) # Blocking
            # print(f'Connection to {Client} ended')
            events = selector.select()
            for key, mask in events:
                key.data(key.fileobj, mask)
