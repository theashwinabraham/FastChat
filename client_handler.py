def parse_message(message):
    l =  message.split()
    return [int(l[0]), l[1]]

class client_handler:
    message_dump = []
    active_threads = []
    def __init__(self) :
        self.message_buffer = []

    def multi_threaded_client(self, connection):
        connection.send(str.encode('Server is working:'))
        while True:
            data = connection.recv(2048)
            if not data:
                break
            # self.message_buffer.append(data.decode('utf-8'))
            self.message_dump.append(parse_message(data.decode('utf-8')))
            
        print("closing the connection")
        connection.close()
    
    def display_messages(self):
        while True:
            if(self.message_buffer != []):
                while len(self.message_buffer):
                    print("Message from the display_message thread: ", self.message_buffer[0])
                    self.active_threads[self.message_buffer[0][0]][3].sendall(str.encode(self.message_buffer[0][1]))
                    self.message_buffer = self.message_buffer[1:]
    @classmethod
    def send_messages(cls):
        while True:
            while len(cls.message_dump):
                cls.active_threads[cls.message_dump[0][0]][0].message_buffer.append(cls.message_dump[0])
                cls.message_dump = cls.message_dump[1:]