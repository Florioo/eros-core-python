from eros import ErosTransport
import socket

class ErosUDP(ErosTransport):
    framing = False
    verification = False
    
    def __init__(self, ip:str, port:int,**kwargs) -> None:
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
    
    def read(self) -> bytes:
        return self.sock.recv(1500)
    
    def write(self, data:bytes):
        self.sock.sendto(data, (self.ip, self.port))
        
