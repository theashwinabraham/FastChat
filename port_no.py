from socket import *
# from typing_extensions import Self

class port_selector:
    port_no = -1
    @classmethod
    def select_port_number(cls):
        if(cls.port_no != -1): return cls.port_no
        port_num = 9000
        host = '127.0.0.1'
        while True:
            try:
                S = socket()
                S.bind((host, port_num))
                S.close() 
                break
            except Exception as error:
                S.close()
                print(error)
                port_num += 100
                continue
        cls.port_no = port_num
        return cls.port_no