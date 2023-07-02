from .drv_generic import ErosTransport, TransportStates
import multiprocessing as mp
# import multiprocessing.connection 
# Enum type
class ResponseType():
    PART_A = 0
    PART_B = 1
    LOOPBACK = 2

pipes = {}
class ErosSerialSim(ErosTransport):
    
    # tx_pipe: mp.connection.PipeConnection
    # rx_pipe: mp.connection.PipeConnection
    
    def __init__(self, name, channel_type: ResponseType,**kwargs) -> None:
        super().__init__(**kwargs)
        self.state = TransportStates.CONNECTED
        if not name in pipes:
            pipes[name] = mp.Pipe()

        if channel_type == ResponseType.PART_A:
            self.tx_pipe = pipes[name][0]
            self.rx_pipe = pipes[name][0]
        elif channel_type == ResponseType.PART_B:
            self.tx_pipe = pipes[name][1]
            self.rx_pipe = pipes[name][1]
        elif channel_type == ResponseType.LOOPBACK:
            self.tx_pipe = pipes[name][1]
            self.rx_pipe = pipes[name][0]
        
    def read(self):
        return self.rx_pipe.recv()
    
    def write(self, data):
        self.tx_pipe.send(data)
    
   