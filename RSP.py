import multiprocessing as mp
from multiprocessing.connection import Connection
from packeteiser import COBS_PACKETIZER

import logging 
import time
import random
import bitstruct
from dataclasses import dataclass
from enum import Enum
from crc8 import crc8_gen

class RSPType(Enum):
    DATA_ACK   = 0  # Data packet with acknowledgement
    DATA_NOACK = 1  # Data packet without acknowledgement
    RESP_ACK   = 2  # Acknowledgement packet
    RESP_NACK  = 3  # Negative acknowledgement packet
    
    def __str__(self) -> str:
        return self.name 
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class RSPHeader:
    seq: int
    type: RSPType
    
    def pack(self):
        return bitstruct.pack("u8u4u4", self.seq, self.type.value, 0)
    
    @classmethod
    def unpack(cls, data):
        seq, type, reserved = bitstruct.unpack("u8u4u4", data)
        return cls(seq, RSPType(type))
    
@dataclass
class RSPFrame:
    header: RSPHeader
    data: bytes
    
@dataclass
class RSPResponse:
    ok: bool
    data: bytes
    

crc8 = crc8_gen()

class RSP():
    def __init__(self, name:str, port: Connection, log_level=logging.DEBUG):
        """Reliable Serial Protocol

        Args:
            name (str): Name of the connection
            port (Connection): Pipe handle to use for communication
            log_level (optional): Log level. Defaults to logging.DEBUG.
        """
        
        self.log = logging.getLogger(name)
        self.log.setLevel(log_level)
        
        self.port:COBS_PACKETIZER = port
        self.port.received_packet_callback = self.process_received_data

        self.seq = 0
        self.responses = {}
        
    def transmit_frame(self, frame : RSPFrame):
        """ Transmit a frame
        """
        data = frame.header.pack() + frame.data
        self.port.write_packet(data + crc8.get(data))
    
    def wait_for_response(self, seq:int, timeout:float=5) -> RSPFrame:
        """Wait for a response with the specified sequence number

        Args:
            seq (int): Sequence number to wait for
            timeout (float, optional): Timeout in seconds. Defaults to 5.

        Returns:
            RSPFrame: Response frame
        """
        
        start_time = time.time()
        
        while True:
            
            # Check if we have received a response with the specified sequence number
            if seq in self.responses:
                response = self.responses[seq]
                del self.responses[seq]
                return response
            
            if time.time() - start_time > timeout:
                return None
            
            time.sleep(0.01)
            
    def send_packet(self, data:bytes, request_ack: bool) -> RSPResponse:
        """Send a packet

        Args:
            data (bytes): Data to send
            request_ack (bool): Request an acknowledgement

        Returns:
            RSPResponse: Response
        """
        # Increment the sequence number if we are requesting an acknowledgement
        if request_ack:
            self.seq += 1
        
        if self.seq > 255:
            self.seq = 0
            
        # Create the frame
        if request_ack:
            header = RSPHeader(self.seq , RSPType.DATA_ACK)
        else:
            header = RSPHeader(0 , RSPType.DATA_ACK)
            
        frame = RSPFrame(header, data)
        
        # Send the frame
        self.transmit_frame(frame)
        
        if not request_ack:
            return RSPResponse(True, b"")
        
        response: RSPFrame = self.wait_for_response(self.seq)

        if response is None:
            self.log.error("No response received because of timeout")
            return RSPResponse(False, b"Timeout")
        
        if response.header.type == RSPType.RESP_ACK:
            return RSPResponse(True, response.data)
        
        elif response.header.type == RSPType.RESP_NACK:
            return RSPResponse(False, response.data)
        
    def process_received_data(self, data: bytes) -> None:
        header, data, crc = data[:2], data[2:-2], data[-2:]
        
        if crc != crc8.get(header + data):
            self.log.error("CRC error")
            return
        
        # Unpack the frame
        frame = RSPFrame(RSPHeader.unpack(header), data)
        self.process_received_frame(frame)
                
    def process_received_frame(self, frame:RSPFrame):
        
        if frame.header.type == RSPType.DATA_ACK or frame.header.type == RSPType.DATA_NOACK:
            
            ret = self.handle_data(frame.data)
            if frame.header.type != RSPType.DATA_ACK:
                return
            
            type = RSPType.RESP_ACK if ret.ok else RSPType.RESP_NACK
            
            self.transmit_frame(RSPFrame(RSPHeader(frame.header.seq, type), ret.data))
            
        elif frame.header.type == RSPType.RESP_ACK or frame.header.type == RSPType.RESP_NACK:
            self.responses[frame.header.seq] = frame

        
    
    def handle_data(self, data: bytes) -> RSPResponse:
        self.log.info(f"Received: {data}")
        
        if random.randint(0,10) < 5:
            return RSPResponse(False, "A Custom error ".encode())
        
        return RSPResponse(True, "OK".encode())
