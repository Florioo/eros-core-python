from multiprocessing.connection import Connection

from cobs import cobs
import threading
import logging 
import time
import random

class COBS_PACKETIZER():
    def __init__(self, name:str, pipe_handle:Connection, log_level=logging.DEBUG):
        """Packetizer for COBS encoded data

        Args:
            name (str): Name of the packetizer
            pipe_handle (Connection): Pipe handle to use for communication
            log_level (_type_, optional): Log level. Defaults to logging.DEBUG.
        """
        self.log = logging.getLogger(name)
        self.log.setLevel(log_level)
        self.lock = threading.Lock()
        self.pipe:Connection = pipe_handle
        
        
        self.RX_thread = threading.Thread(target=self.read_thread,  daemon=True)
        self.RX_thread.start()
        
        self.TX_thread = threading.Thread(target=self.write_thread, daemon=True)
        self.TX_thread.start()
        
                
        self.received_packet_callback = None
        self.transmit_buffer = b'' # Buffer for data to transmit
        self.receive_buffer = b'' # Buffer for data received from the pipe
        
    def write_packet(self, data: bytes) -> None:
        """Transmit packet over the pipe

        Args:
            data (bytes): Data to transmit
        """
        with self.lock:
            self.log.info(f"Transmitting: {data}")
            encoded = cobs.encode(data) + b'\x00'
            
            # cobs.decode(encoded[:-1]) # Check if the data is valid
            self.transmit_buffer += encoded
        self.flush()
        
        
    def flush(self):
        """Flush the transmit buffer to the pipe
        """
        with self.lock:
            # split into random chunks, to emulate real world data streaming in
            while len(self.transmit_buffer) > 0:
                chunk_size = random.randint(1,10)
                self.pipe.send(self.transmit_buffer[:chunk_size])
                self.transmit_buffer = self.transmit_buffer[chunk_size:]
                
            self.transmit_buffer = b''
        
    def write_thread(self):
        """ Thread for periodically flushing the transmit buffer
        """
        while True:
            time.sleep(0.01)
            if len(self.transmit_buffer) > 0:
                self.flush()
            
    def read_thread(self):
        """ Thread for reading data from the pipe
        """
        while True:
            data = self.pipe.recv()            
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
                self.received_packet_callback(packet)