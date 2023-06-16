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
        """Packetizer for COBS encoded data

        Args:
            name (str): Name of the packetizer
            pipe_handle (Connection): Pipe handle to use for communication
            log_level (_type_, optional): Log level. Defaults to logging.DEBUG.
        """
        self.receive_buffer = b""
        
    def pack(self, data: bytes) -> None:
        """Transmit packet over the pipe

        Args:
            data (bytes): Data to transmit
        """
        encoded = cobs.encode(data) + b'\x00'
        
        return encoded
            

    def unpack(self, data: bytes) -> List[bytes]:
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
    
        packets = [cobs.decode(packet) for packet in packets]
        return packets

    
class Verification():
    def __init__(self) -> None:
        
        config = crc.Configuration(
            width=16,
            polynomial=0x07,
            init_value=0x00,
            final_xor_value=0x00,
            reverse_input=False,
            reverse_output=False,
        )
        self.crc16 = crc.Calculator(config)
        
    def pack(self, data: bytes) -> bytes:
        # Add CRC to the data
        return data + self.crc16.checksum(data).to_bytes(2,'big')
    
    def unpack(self, data: bytes) -> bytes:
        # Check CRC validity
        is_valid = self.crc16.checksum(data) == 0
        
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
    VERISON = 0
    def __init__(self) -> None:
        
        pass
    
    def pack(self, data: bytes, channel:int , request_response: bool) -> bytes:         
        header = RoutingPacketHeader(VERISON=self.VERISON, channel=channel, request_response=request_response, reserved=0).pack()
        return header + data

    def unpack(self, data: bytes) -> Tuple[RoutingPacketHeader, bytes]:
        header = RoutingPacketHeader.unpack(data[:1])
        return header, data[1:]

class Eros():
    def __init__(self) -> None:
        self.framing_layer = Framing()
        self.verification_layer = Verification()
        self.routing_layer = Routing()

        self.channels = [None, None, None, None, None, None, None, None]
        self.transport_layers = []
        
    def transmit_stream(self,transport:int, channel, data: Union[bytes, str]) -> None:
        """Transmit data over the stream

        Args:
            channel (str): Channel name
            data (Union[bytes, str]): Data to transmit
         """
        stream_data = self.framing_layer.pack( self.verification_layer.pack(self.routing_layer.pack(data, channel, False)))
        print(f"Transmitting stream {stream_data}")
        if transport < len(self.transport_layers):
            self.transport_layers[transport].write(stream_data)
        else:
            raise ValueError
        
    def transmit_packet(self, transport:int, channel, data: Union[bytes, str]) -> None:
        stream_data = self.routing_layer.pack(data, channel, False)
        print(f"Transmitting packet {stream_data}")
        if transport < len(self.transport_layers):
            self.transport_layers[transport].write(stream_data)
        else:
            raise ValueError
        
    
    def stream_receive_thread(self, stream) -> None:
        time.sleep(0.5)
        while True:
            data = stream.read()            
            packets = self.framing_layer.unpack(data)
            
            for packet in packets:
                verfied_packet = self.verification_layer.unpack( packet)
                route, content = self.routing_layer.unpack(verfied_packet)

                if self.channels[route.channel] is not None:
                    self.channels[route.channel](content)
                    
                    
    def packet_receive_thread(self, stream) -> None:
        time.sleep(0.5)
        while True:
            packet = stream.read()
            route, content = self.routing_layer.unpack(packet)

            if self.channels[route.channel] is not None:
                self.channels[route.channel](content)
                            
        
    def attach_channel_callback(self, channel:int, callback: callable) -> None:
        self.channels[channel] = callback
    
    def add_stream_transport_layer(self, stream):
        
        # Register the transport layer
        self.transport_layers.append(stream)
        
        # Start receive thread
        thread_handle = threading.Thread(target=self.stream_receive_thread, args=(stream,), daemon=True)
        thread_handle.start()
        
        return len(self.transport_layers) - 1

    def add_packet_transport_layer(self, stream):
        
        # Register the transport layer
        self.transport_layers.append(stream)
        
        # Start receive thread
        thread_handle = threading.Thread(target=self.packet_receive_thread, args=(stream,), daemon=True)
        thread_handle.start()
        
        return len(self.transport_layers) - 1
    
        
import stream_simulator
import packet_transport_simulator
def tracing_handler(data):
    print(f"Received {data}")
    
eros = Eros()

class channels:
    CHANNEL1 = 1
    
serial_loopback = stream_simulator.SerialSimulator("test",          stream_simulator.ChannelType.LOOPBACK)
udp_loopback = packet_transport_simulator.PacketSimulator("test",   packet_transport_simulator.ChannelType.LOOPBACK)


eros.attach_channel_callback(channels.CHANNEL1, tracing_handler)
serial1_handle = eros.add_stream_transport_layer(serial_loopback)
udp1_handle = eros.add_packet_transport_layer(udp_loopback)

eros.transmit_stream(serial1_handle, channels.CHANNEL1, b"test")
eros.transmit_stream(serial1_handle, channels.CHANNEL1, b"testq")
eros.transmit_stream(serial1_handle, channels.CHANNEL1, b"testr")
eros.transmit_packet(udp1_handle,    channels.CHANNEL1, b"tesasdqwqwdqwdqwdtr")
eros.transmit_packet(udp1_handle,    channels.CHANNEL1, b"tesawqdsdqwqwdqwdqwdtr")


time.sleep(1)

