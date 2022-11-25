import socket
import time
class Message:
    """Class implementing the messaging protocol.

    While sending, first, the size of the message is sent with a fixed size of 8 bytes. Next, the messsage is sent.

    While receiving, first, the size is received, and then the appropriate number bytes are received for the actual message.
    """
    #stores the maximum length of the size of the message represented in binary
    PRE_MSG_SIZE = 8
    MAX_PACKET_SZ = 4096   
    MSG_LATENCY = 0.1 #models the time taken by an actual network to transfer data    
    current_throughput = 0 
    @classmethod
    def send(cls, msg: bytes, conn: socket.socket) -> bool:
        """Sends the message to the server/client along with the message size.

        :param msg: message to be sent
        :type msg: bytes
        :param conn: connection with the server/client
        :type conn: socket.socket
        :return: True if the message is within the size limit of 10^8 bytes, false otherwise.
        :rtype: bool
        """
        time.sleep(cls.MSG_LATENCY)
        sz = str(len(msg))
        if(len(sz) > cls.PRE_MSG_SIZE):
            return False
        cls.current_throughput += int(sz)
        conn.sendall(sz.zfill(cls.PRE_MSG_SIZE).encode())
        conn.sendall(msg)
        return True
    @classmethod
    def recv(cls, conn: socket.socket) -> bytes:
        """receives the message from the server/client.

        :param conn: connection with the server/client
        :type conn: socket.socket
        :raises RuntimeError: raised if the connection is broken while receiving
        :return: returns the received message
        :rtype: bytes
        """
        sz = conn.recv(cls.PRE_MSG_SIZE)
        if not sz:
            return sz
        sz = int(sz)
        cls.current_throughput += sz
        bytes_recd = 0
        message = b""
        while bytes_recd < sz:
            chunk = conn.recv(min(sz - bytes_recd, cls.MAX_PACKET_SZ))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            message += chunk
            bytes_recd = bytes_recd + len(chunk)
        return message