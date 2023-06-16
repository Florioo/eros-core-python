from multiprocessing.connection import Connection
from cobs import cobs
import threading
import logging 
import time

class framing():
    def __init__(self, name:str, io, log_level=logging.DEBUG):
        """Packetizer for COBS encoded data

        Args:
            name (str): Name of the packetizer
            pipe_handle (Connection): Pipe handle to use for communication
            log_level (_type_, optional): Log level. Defaults to logging.DEBUG.
        """
        
        self.log = logging.getLogger(name)
        self.log.setLevel(log_level)

        self.io = io
                
        self.RX_thread = threading.Thread(target=self.read_thread,  daemon=True)
        self.RX_thread.start()
                
        self.received_packet_callback = None
        self.receive_buffer = b'' # Buffer for data received from the pipe

    def write_packet(self, data: bytes) -> None:
        """Transmit packet over the pipe

        Args:
            data (bytes): Data to transmit
        """
        self.log.info(f"Transmitting: {data}")
        encoded = cobs.encode(data) + b'\x00'
        
        # Check if the data is valid
        self.io.write(encoded)
    
            
    def read_thread(self):
        """ Thread for reading data from the pipe
        """
        while True:
            data = self.io.read()            
            self.process_data(data)
            
    def process_data(self, data: bytes):
        """Process data received from the pipe

        Args:
            data (bytes): Data received from the pipe
        """
        
        # Add the data from last transmission to the buffer
        data = self.receive_buffer + data
        
        # Split data into null terminated chunks
        packets = data.split(b'\x00')
        
        # Add the last chunk to the buffer, because it may be incomplete
        self.receive_buffer = packets.pop()
        
        # Process each chunk
        for packet in packets:
            if self.received_packet_callback is not None:
                self.received_packet_callback(cobs.decode(packet))