from queue import Queue

# Enum type
class ChannelType():
    PART_A = 0
    PART_B = 1
    LOOPBACK = 2

pipes = {}
class PacketSimulator():
    tx_pipe: Queue
    rx_pipe: Queue
    
    def __init__(self, name:str, channel_type: ChannelType) -> None:
        if not name in pipes:
            pipes[name] = (Queue(), Queue())

        if channel_type == ChannelType.PART_A:
            self.tx_pipe = pipes[name][0]
            self.rx_pipe = pipes[name][1]
        elif channel_type == ChannelType.PART_B:
            self.tx_pipe = pipes[name][1]
            self.rx_pipe = pipes[name][0]
        elif channel_type == ChannelType.LOOPBACK:
            self.tx_pipe = pipes[name][0]
            self.rx_pipe = pipes[name][0]
        
    def read(self):
        return self.rx_pipe.get()
    
    def write(self, data):
        self.tx_pipe.put(data)
         