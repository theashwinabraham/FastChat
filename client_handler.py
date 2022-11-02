def parse_message(message):
    l =  message.split("\n")
    return [int(l[0]), l[1]]

#class to handle the clients(to receive and distribute messages)
class client_handler:
    #stores all the messages that are to be dispatched
    message_dump = []
    #stores all the active threads
    active_threads = []
    def __init__(self) :
        #stores the pending messages to be sent to each client
        self.message_buffer = []
    #waits and receives messages from the client
    def multi_threaded_client(self, connection):
        connection.send(str.encode('Server is working:'))
        while True:
            data = connection.recv(2048)
            if not data:
                break
            self.message_dump.append(parse_message(data.decode('utf-8')))
        print("closing the connection")
        connection.close()
    #sends the messages to the client
    def send_messages(self):
        while True:
            if(self.message_buffer != []):
                while len(self.message_buffer):
                    print("Message from the display_message thread: ", self.message_buffer[0])
                    self.active_threads[self.message_buffer[0][0]][3].sendall(str.encode(self.message_buffer[0][1]))
                    self.message_buffer = self.message_buffer[1:]
    @classmethod
    def distribute_messages(cls):
        while True:
            while len(cls.message_dump):
                cls.active_threads[cls.message_dump[0][0]][0].message_buffer.append(cls.message_dump[0])
                cls.message_dump = cls.message_dump[1:]