from .main import ErosTransport
from multiprocessing.connection import Connection
import multiprocessing as mp

# Enum type
class ChannelType():
    PART_A = 0
    PART_B = 1
    LOOPBACK = 2

pipes = {}
class ErosSerialSim(ErosTransport):
    
    tx_pipe: mp.connection.PipeConnection
    rx_pipe: mp.connection.PipeConnection
    
    def __init__(self, name, channel_type: ChannelType,**kwargs) -> None:
        super().__init__(**kwargs)
        
        if not name in pipes:
            pipes[name] = mp.Pipe()

        if channel_type == ChannelType.PART_A:
            self.tx_pipe = pipes[name][0]
            self.rx_pipe = pipes[name][0]
        elif channel_type == ChannelType.PART_B:
            self.tx_pipe = pipes[name][1]
            self.rx_pipe = pipes[name][1]
        elif channel_type == ChannelType.LOOPBACK:
            self.tx_pipe = pipes[name][1]
            self.rx_pipe = pipes[name][0]
        
    def read(self):
        return self.rx_pipe.recv()
    
    def write(self, data):
        self.tx_pipe.send(data)
         