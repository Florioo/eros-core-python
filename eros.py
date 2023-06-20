import logging
from cobs import cobs
from typing import Union, List, Tuple
import crc
import bitstruct
from dataclasses import dataclass
import threading
import time

class Framing():
    def __init__(self):
        """Framing layer for the eros system
        """
        self.receive_buffer = b""
        
    def pack(self, data: bytes) -> bytes:
        """Pack the data into a cobs encoded frame

        Args:
            data (bytes): Data to pack
        
        Returns:
            bytes: Unpacked data
        """
        encoded = cobs.encode(data) + b'\x00'
        
        return encoded
            

    def unpack(self, data: bytes) -> List[bytes]:
        """Unpack the the result from a stream into packets
           Will return a empty list if it did not contain valid packets

        Args:
            data (bytes): Data to unpack
        
        Returns:
            List[bytes]: List of data packets
        """
        
        # Add the data from last transmission to the buffer
        data = self.receive_buffer + data
        
        # Split data into null terminated chunks
        packets = data.split(b'\x00')
        
        # Add the last chunk to the buffer, because it may be incomplete
        self.receive_buffer = packets.pop()
        
        packets = [cobs.decode(packet) for packet in packets]

        return packets

class Verification():
    """Verification layer for the eros system
    """
    def __init__(self) -> None:
        
        # config = crc.Configuration(
        #     width=16,
        #     polynomial=0x07,
        #     init_value=0x00,
        #     final_xor_value=0x00,
        #     reverse_input=False,
        #     reverse_output=False,
        # )
        # self.crc16 = crc.Calculator(config)
        pass
    def crc16(self, data):
        crc = 0xFFFF
        polynomial = 0x8005

        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                # Ensure a 2-byte result
                crc &= 0xFFFF 
        return crc
    
    def pack(self, data: bytes) -> bytes:
        """ Add CRC to the data

        Args:
            data (bytes): Data to add CRC to

        Returns:
            bytes: Data with CRC
        """
        # Add CRC to the data
        # return data + self.crc16.checksum(data).to_bytes(2,'big')
        return data + self.crc16(data).to_bytes(2,'big')
    
    def unpack(self, data: bytes) -> bytes:
        """Verify CRC and remove it from the data

        Args:
            data (bytes): Data to verify CRC

        Raises:
            ValueError: If CRC is invalid 

        Returns:
            bytes: Data without CRC
        """
        # Check CRC validity
        # is_valid = self.crc16.checksum(data) == 0
        is_valid = self.crc16(data) == 0
        
        if len(data) < 2:
            is_valid = False
        
        if not is_valid:
            raise ValueError("Invalid CRC")
            
        # Return data without CRC
        return data[:-2]

@dataclass
class RoutingPacketHeader:
    VERISON: int
    channel: int
    request_response: bool
    reserved: int
    
    def pack(self) -> bytes:         
        return bitstruct.pack( "u2u4u1u1", self.VERISON, self.channel, self.request_response, self.reserved)
    
    @classmethod
    def unpack(cls, data: bytes):
        cls.VERISON, cls.channel, cls.request_response, cls.reserved = bitstruct.unpack( "u2u4u1u1", data)
        return cls
       
class Routing():
    """Routing layer for the eros system
    """
    VERISON = 0
    def __init__(self) -> None:
        pass
    
    def pack(self, data: bytes, channel:int , request_response: bool) -> bytes:     
        """ Pack the routing layer
        
        Args:
            data (bytes): Data to pack
            
        Returns:
            bytes: Data with routing layer
        """
        header = RoutingPacketHeader(VERISON=self.VERISON, channel=channel, request_response=request_response, reserved=0).pack()
        return header + data

    def unpack(self, data: bytes) -> Tuple[RoutingPacketHeader, bytes]:
        """Unpack the routing layer

        Args:
            data (bytes): Data to unpack

        Returns:
            Tuple[RoutingPacketHeader, bytes]: Tuple of header and data
        """
        header = RoutingPacketHeader.unpack(data[:1])
        return header, data[1:]

class Eros():
    def __init__(self) -> None:
        self.framing_layer = Framing()
        self.verification_layer = Verification()
        self.routing_layer = Routing()
        self.channels = [None, None, None, None, None, None, None, None]
        
    def attach_channel_callback(self, channel:int, callback: callable) -> None:
        self.channels[channel] = callback

class ErosStream(Eros):
    def __init__(self, stream) -> None:
        
        super().__init__()
        
        self.stream = stream 
        
        # Start receive thread
        thread_handle = threading.Thread(target=self.receive_thread, daemon=True)
        thread_handle.start()
        
    def transmit(self, channel:int, data: Union[bytes, str]) -> None:
        """Transmit data over the stream

        Args:
            channel (int): Channel number
            data (Union[bytes, str]): Data to transmit
         """
         
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        stream_data = self.framing_layer.pack( self.verification_layer.pack(self.routing_layer.pack(data, channel, False)))
        self.stream.write(stream_data)
    
    def receive_thread(self) -> None:
        """Receive thread, will call the channel callbacks with the data
        """
        time.sleep(0.5)
        while True:
            data = self.stream.read()            
            try:
                packets = self.framing_layer.unpack(data)
                
                for packet in packets:
                    verfied_packet = self.verification_layer.unpack( packet)
                    route, content = self.routing_layer.unpack(verfied_packet)

                    if self.channels[route.channel] is not None:
                        self.channels[route.channel](content)
            except Exception as e:
                print(e)
                print("Error", data)
                

class ErosPacket(Eros):
    def __init__(self, stream) -> None:
        super().__init__()

        self.stream = stream 
        
        # Start receive thread
        thread_handle = threading.Thread(target=self.receive_thread, daemon=True)
        thread_handle.start()
        
    def transmit(self,channel, data: Union[bytes, str]) -> None:
        """Transmit data over the stream

        Args:
            channel (int): Channel number
            data (Union[bytes, str]): Data to transmit
         """
         
        if isinstance(data, str):
            data = data.encode('utf-8')
         
        stream_data = self.routing_layer.pack(data, channel, False)
        self.stream.write(stream_data)
    
    def receive_thread(self) -> None:
        """Receive thread, will call the channel callbacks with the data
        """
        time.sleep(0.5)
        while True:
            data = self.stream.read()            
            route, content = self.routing_layer.unpack(data)

            if self.channels[route.channel] is not None:
                self.channels[route.channel](content)
