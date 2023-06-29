from typing import Union, List, Tuple
import threading
from .eros_layers import Framing, Verification, RoutingPacketHeader, Routing  # Make sure you import the correct module
from . import eros_layers
import cobs
import copy
import logging
import time

class ErosTransport():
    framing = True
    verification = True
    
    def __init__(self,log_level = logging.INFO):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(log_level)
        
    def write(self, data: bytes) -> None:
        pass
    
    def read(self) -> bytes:
        pass
    
class Eros():
    framing_layer = None
    verification_layer = None
    
    def __init__(self, transport_handle:ErosTransport,log_level = logging.INFO) -> None:
        self.transport_handle = transport_handle
        self.channels = {}
        self.discart_buffer = b""
        
        self.log = logging.getLogger("Eros")
        self.log.setLevel(log_level)
        
        self.log.info(f"Initializing Eros, verification: {self.transport_handle.verification}, framing: {self.transport_handle.framing}")
        if self.transport_handle.framing:
            self.framing_layer = Framing()
            
        if self.transport_handle.verification:
            self.verification_layer = Verification()
    
        self.routing_layer = Routing()
            
        # Start receive thread
        self.thread_handle = threading.Thread(target=self.receive_thread, daemon=True)
        self.thread_handle.start()
        
    def attach_channel_callback(self, channel:int, callback: callable) -> None:
        """Attach a callback to a channel
        
        If a callback is already attached to the channel it will be overwritten
           
        Args:
            channel (int): Channel number
            callback (callable): Callback function
        """
        self.log.info(f"Attaching callback to channel {channel}, callback: {callback}")
        self.channels[channel] = callback

    def transmit_packet(self, channel:int, data: Union[bytes, str]) -> None:
        """Transmit data over the stream

        Args:
            channel (int): Channel number
            data (Union[bytes, str]): Data to transmit
         """
         
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        # Make a copy in memory
        data = copy.copy(data)
    
        data = self.routing_layer.pack(data, 0, channel, False)
    
        if self.verification_layer is not None:
            data = self.verification_layer.pack(data)
    
        if self.framing_layer is not None:            
            data = self.framing_layer.pack(data)
            
        self.transport_handle.write(data)
    
    def receive_thread(self) -> None:
        """Receive thread, will call the channel callbacks with the data, 1 thread per Eros instance
        """
        while True:
            self.receive_packets()  
         
            # except Exception as e:
            #     # Todo add better error handling
            #     print("error:" + str(e))

    def receive_packets(self) -> None:    
        # Call must be blocking
        try:
            data = self.transport_handle.read()
            
            if self.framing_layer is not None:
                packets = self.framing_layer.unpack(data)
            else:
                packets = [data]
        
            for packet in packets:

                if self.verification_layer is not None:
                    packet = self.verification_layer.unpack( packet)
                
                route, content = self.routing_layer.unpack(packet)

                if self.channels.get(route.channel) is not None:
                    self.channels[route.channel](content)
                    
        except eros_layers.CRCException:
            self.discart_buffer += data

        except cobs.cobs.DecodeError:
            self.discart_buffer += data
    
    def log_exceptions(self) -> None:    
        
        if len(self.discart_buffer) == 0:
            return
         
        self.log.warning(f"{len(self.discart_buffer)} bytes were discarded due to Encoding/Decoding errors")
        self.log.warning(f"last 64 bytes of Discarded data:\n{self.discart_buffer[-100:]}")
        self.discart_buffer = b""
         
    
    def spin(self, log_exceptions=False):
        
        while True:

            if log_exceptions:
                self.log_exceptions()

            if not self.thread_handle.is_alive():
                return
            
            time.sleep(1)