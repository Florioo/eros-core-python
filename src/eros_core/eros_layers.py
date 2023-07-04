from cobs import cobs
from typing import List, Tuple
import bitstruct
from dataclasses import dataclass

class CRCException(Exception):
    pass

class COBSException(Exception):
    pass

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
        
        # If one of the packets fails to decode, just return the raw data
        outgoing_packets = []
        for packet in packets:
            try:
                outgoing_packets.append(cobs.decode(packet))
            except cobs.DecodeError:
                outgoing_packets.append(packet)
                
        # Remove empty packets
        outgoing_packets = [packet for packet in outgoing_packets if packet != b'']
        
        return outgoing_packets

class Verification():
    """Verification layer for the eros system
    """
    def __init__(self) -> None:
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
            raise CRCException(f"CRC is invalid: {self.crc16(data)}")
            
        # Return data without CRC
        return data[:-2]

@dataclass
class RoutingPacketHeader:
    version: int
    channel: int
    request_response: bool
    reserved: int
    
    def pack(self) -> bytes:         
        return bitstruct.pack( "u2u4u1u1", self.version, self.channel, self.request_response, self.reserved)
    
    @classmethod
    def unpack(cls, data: bytes):
        cls.version, cls.channel, cls.request_response, cls.reserved = bitstruct.unpack( "u2u4u1u1", data)
        return cls
       
class Routing():
    """Routing layer for the eros system
    """
    def __init__(self) -> None:
        pass
    
    def pack(self, data:bytes, version:int, channel:int , request_response: bool) -> bytes:     
        """ Pack the routing layer
        
        Args:
            data (bytes): Data to pack
            
        Returns:
            bytes: Data with routing layer
        """
        header = RoutingPacketHeader(version=version, channel=channel, request_response=request_response, reserved=0).pack()
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
