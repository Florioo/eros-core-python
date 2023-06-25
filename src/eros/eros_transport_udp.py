from eros import ErosTransport
import socket
import time

class ErosUDP(ErosTransport):
    framing = True
    verification = True
    
    def __init__(self, ip:str, port:int,**kwargs) -> None:
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
        self.sock.bind(("0.0.0.0", self.port))  

    def read(self) -> bytes:
        
        self.log.debug(f"Listening on {self.ip}:{self.port}")
        data, addr = self.sock.recvfrom(1024)  # read data from the socket


        self.log.debug(f"Received: {data}")
        return data
    
    def write(self, data:bytes):
        self.log.debug(f"Transmitting: {data}")
        self.sock.sendto(data, (self.ip, self.port))
        
