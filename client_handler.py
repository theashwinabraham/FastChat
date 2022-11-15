import threading

def parse_message(message):
    l =  message.split("\n")
    return [l[0], l[1]]

#class to handle the clients(to receive and distribute messages)
class client_handler:
    #stores all the messages that are to be dispatched
    message_dump = []
    #stores all the active threads
    active_threads = dict()
    def __init__(self, name) :
        #stores the pending messages to be sent to each client
        self.message_buffer = []
        self.client_name = name
    #waits and receives messages from the client
    def multi_threaded_client(self, connection):
        connection.send(str.encode('Server is working:'))
        while True:
            data = connection.recv(2048)
            if not data:
                break  
            L = parse_message(data.decode('utf-8'))
            L.append(self.client_name)
            self.message_dump.append(L)
        print("closing the connection")
        self.active_threads.pop(self.client_name)
        connection.close()
    #sends the messages to the client
    def send_messages(self):
        while True:
            if(self.message_buffer != []):
                while len(self.message_buffer):
                    print("Message from the display_message thread: ", self.message_buffer[0])
                    self.active_threads[self.message_buffer[0][0]][3].sendall(str.encode(self.message_buffer[0][2] + "\n" + self.message_buffer[0][1]))
                    self.message_buffer = self.message_buffer[1:]
    @classmethod
    def distribute_messages(cls):
        while True:
            while len(cls.message_dump):
                print(len(cls.message_dump))
                print(cls.message_dump[0], flush=True)
                cls.active_threads[cls.message_dump[0][0]][0].message_buffer.append(cls.message_dump[0])
                cls.message_dump = cls.message_dump[1:]
    @classmethod
    def getClientName(cls, Client):
        print("getting client name", flush=True)
        name = bytes.decode(Client.recv(1024))
        obj = client_handler(name)
        t = threading.Thread(target = client_handler.multi_threaded_client, args = (obj, Client))
        t.start()
        t1 = threading.Thread(target = client_handler.send_messages, args = (obj, ))
        t1.start()
        client_handler.active_threads[name] = (obj, t, t1, Client)
        print(client_handler.active_threads, flush=True)