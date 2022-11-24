import socket

class Message:
    #stores the maximum length of the size of the message represented in binary
    PRE_MSG_SIZE = 8
    MAX_PACKET_SZ = 4096        
    @classmethod
    def send(cls, msg: bytes, conn: socket.socket) -> bool:
        sz = str(len(msg))
        if(len(sz) > cls.PRE_MSG_SIZE):
            return False
        conn.sendall(sz.zfill(cls.PRE_MSG_SIZE).encode())
        conn.sendall(msg)
        return True
    @classmethod
    def recv(cls, conn: socket.socket) -> bytes:
        sz = int(conn.recv(cls.PRE_MSG_SIZE))
        bytes_recd = 0
        message = b""
        while bytes_recd < sz:
            chunk = conn.recv(min(sz - bytes_recd, cls.MAX_PACKET_SZ))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            message += chunk
            bytes_recd = bytes_recd + len(chunk)
        return message