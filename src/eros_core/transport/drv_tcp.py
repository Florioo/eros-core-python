from .drv_generic import ErosTransport
import socket

class ErosTCP(ErosTransport):
    framing = True
    verification = True
    def __init__(self,ip:str, port:int,**kwargs) -> None:
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        self.sock.connect((ip, port))
    
    def read(self):
        return self.sock.recv(1024)
    
    def write(self, data):
        self.sock.send(data)
        
