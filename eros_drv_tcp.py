import time
from eros import ErosStream, ErosPacket
from typing import List
from dataclasses import dataclass
import socket

class ErosTCP():
    def __init__(self,ip,port) -> None:
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        self.sock.connect((ip, port))
    
    def read(self):
        return self.sock.recv(1024)
    
    def write(self, data):
        self.sock.send(data)
        
