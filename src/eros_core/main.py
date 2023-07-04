from typing import Union, List, Tuple, Dict
import threading
from .eros_layers import Framing, Verification, RoutingPacketHeader, Routing  # Make sure you import the correct module
from . import eros_layers
import cobs
import copy
import logging
import time
from dataclasses import dataclass, field
from .eros_analytics import ErosStreamAnalytics
from .transport.drv_generic import ErosTransport,TransportStates
import copy
class Eros():
    framing_layer = None
    verification_layer = None
    kill_receive_thread = False
    
    def __init__(self, transport_handle:ErosTransport,log_level = logging.INFO) -> None:
        self.transport_handle = transport_handle
        self.channels = {}
        self.raw_callback = None
        self.catch_callback = None
        self.fail_callback = None
        
        self.analytics: Dict[int, Tuple[ErosStreamAnalytics,ErosStreamAnalytics]] = {}
        self.analytics[-1] = (ErosStreamAnalytics(),ErosStreamAnalytics())
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

    def attach_catch_callback(self, callback: callable) -> None:
        """Attach a callback to a channel
        
        If a callback is already attached to the channel it will be overwritten
           
        Args:
            channel (int): Channel number
            callback (callable): Callback function
        """
        self.log.info(f"Attaching catch callback, callback: {callback}")
        self.catch_callback = callback
        
    def attach_fail_callback(self, callback: callable) -> None:
        """Attach a callback to a channel
        
        If a callback is already attached to the channel it will be overwritten
           
        Args:
            channel (int): Channel number
            callback (callable): Callback function
        """
        self.log.info(f"Attaching fail callback, callback: {callback}")
        self.fail_callback = callback
        
    def attach_raw_callback(self, callback: callable) -> None:
        self.log.info(f"Attaching raw callback, callback: {callback}")
        self.raw_callback = callback
        
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
    
        if channel is not None:
            data = self.routing_layer.pack(data, 0, channel, False)
    
        if self.verification_layer is not None:
            data = self.verification_layer.pack(data)
    
        if self.framing_layer is not None:            
            data = self.framing_layer.pack(data)
        
        # Set TX Analytics
        if channel not in self.analytics:
            self.analytics[channel] = (ErosStreamAnalytics(),ErosStreamAnalytics())
        self.analytics[channel][1].register_data(len(data))
        
        self.transport_handle.write(data)
        
    
    def receive_thread(self) -> None:
        """Receive thread, will call the channel callbacks with the data, 1 thread per Eros instance
        """
        while True:
            if self.kill_receive_thread:
                return
            self.receive_packets()  

    def receive_packets(self) -> None:    
        # Call must be blocking

        raw_data = self.transport_handle.read()
        
        if self.transport_handle.get_state() == TransportStates.DEAD:
            self.log.error("Transport layer is dead, killing receive thread")
            self.kill_receive_thread = True
            return
        
        if raw_data is None:
            self.log.debug("Received None from transport layer")
            return
        
        data = copy.copy(raw_data)
        
        if self.framing_layer is not None:
            packets = self.framing_layer.unpack(data)
        else:
            packets = [data]
    
        for unverified_packet in packets:
            try:
                
                if self.verification_layer is not None:
                    verified_packet = self.verification_layer.unpack( unverified_packet)
                else:
                    verified_packet = unverified_packet
                    
                if self.raw_callback is not None:
                    self.raw_callback(verified_packet)
                    
                route, content = self.routing_layer.unpack(verified_packet)

                # Set TX Analytics
                if route.channel not in self.analytics:
                    self.analytics[route.channel] = (ErosStreamAnalytics(),ErosStreamAnalytics())
                self.analytics[route.channel][0].register_data(len(unverified_packet) + 2)
        
                # Call the callback
                if self.channels.get(route.channel) is not None:
                    self.channels[route.channel](content)
                    
                # Otherwise Call the catch callback
                elif self.catch_callback is not None:
                    self.catch_callback(route.channel, content)
                    
            except eros_layers.CRCException:
                
                if self.fail_callback is not None:
                    self.fail_callback(unverified_packet)
                
                self.discart_buffer += unverified_packet
                self.analytics[-1][0].register_data(len(unverified_packet))

            except cobs.cobs.DecodeError:
                
                if self.fail_callback is not None:
                    self.fail_callback(unverified_packet)
                    
                self.discart_buffer += unverified_packet
                self.analytics[-1][0].register_data(len(unverified_packet))

                        

            
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
    
    def get_state(self) -> TransportStates:
        return self.transport_handle.get_state()
    
    def close(self):
        # Close the transport layer
        self.log.info("Closing Eros transport layer")
        self.transport_handle.close()
    
    def wait_for_state(self, state:TransportStates, timeout=2) -> bool:
        return self.transport_handle.wait_for_state(state, timeout)
        