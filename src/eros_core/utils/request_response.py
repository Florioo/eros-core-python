from eros_core import Eros
import logging
from queue import Queue
# Enum
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

class ResponseType(Enum):
    DATA = 0
    ACK = 1
    NACK = 2
    TIMEOUT = 3

@dataclass
class CommandFrame():
    resp_type: ResponseType
    data: bytes
    
    def pack(self) -> bytes:
        return self.resp_type.to_bytes(1, byteorder='big') + self.data

    @staticmethod
    def unpack( data: bytes):
        return CommandFrame(ResponseType(data[0]), data[1:])
    
    def __repr__(self) -> str:
        return __str__(self)
    
    def __str__(self) -> str:
        return f"CommandFrame(type={self.resp_type}, data={self.data})"

class CLIResponse():
    receive_packets_queue = None
    
    def __init__(self, eros: Eros, channel: int, packet_callback: Callable[None, CommandFrame]=None, enable_queue=False) -> None:
        self.eros = eros
        self.channel = channel
        self.packet_callback = packet_callback
        
        if enable_queue:
            self.receive_packets_queue = Queue()
        
        self.eros.attach_channel_callback(self.channel, self.receive_callback)
            
        self.received_data = b""
    
    def receive_callback(self, raw_data: str) -> None:
        """ Callback for receive, it puts the data in the queue

        Args:
            data (str): data received
        """
        
        # Wait for the response  
        frame = CommandFrame.unpack(raw_data)

        # Append the data
        self.received_data = self.received_data + frame.data

        # If the packet is not a data packet, the packed is finished
        if frame.resp_type == ResponseType.DATA:
            return
        # Create the full frame
        full_frame = CommandFrame(frame.resp_type, self.received_data)
        
        # Send the full frame to the queue and/or callback
        if self.receive_packets_queue is not None:
            self.receive_packets_queue.put(full_frame)
            
        if self.packet_callback is not None:
            self.packet_callback(full_frame)
        
        self.received_data = b""
      
    def flush(self) -> None:
        """ Flush the receive data buffer 
        """
        self.received_data = b""
        if self.receive_packets_queue is not None:
            while not self.receive_packets_queue.empty():
                self.receive_packets_queue.get()
                
    def receive_packet(self, timeout=0.15) -> CommandFrame:
        if self.receive_packets_queue is None:
            raise Exception("No receive queue defined")
        
        try:
            return self.receive_packets_queue.get(timeout=timeout)
        except Exception as e:
            return CommandFrame(ResponseType.TIMEOUT, b"")
    
    def send(self, data: str) -> CommandFrame:
        """ Send data and wait for response
        
        Args:
            data (str): Data to send

        Returns:
            str: Data received as a response
        """
        # First flush the receive queue
        self.flush()

        # Transmit the data
        self.eros.transmit_packet(self.channel, data.encode())
      

# from eros import Eros 
# from blessed import Terminal
# import threading
# import time
# from queue import Queue

# class ErosTerminal():
#     def __init__(self, eros:Eros, main_channel, aux_channel) -> None:
#         self.eros = eros
#         self.main_channel = main_channel
#         self.aux_channel = aux_channel

#         self.main_receive_buffer = b""
#         self.main_transmit_queue = Queue()
                
#         self.eros.attach_channel_callback(self.main_channel, self.receive_main)
#         self.eros.attach_channel_callback(self.aux_channel, self.receive_aux)
       
#         self.transmit_thread_handle = threading.Thread(target=self.transmit_thread, daemon=True)
        
#     def transmit_thread(self):
#         last_transmit = time.time()
#         while True:
#             buffer = bytearray()
            
#             # If we are repeatedlt transmitting, wait a bit
#             if time.time() - last_transmit < 0.025:
#                 time.sleep(0.025)
            
#             while True:
#                 buffer += self.main_transmit_queue.get()
#                 if self.main_transmit_queue.empty():
#                     break
            
#             last_transmit = time.time()
#             self.eros.transmit_packet(self.main_channel, bytes(buffer))
        
#     def receive_main(self, data):
#         first_byte = data[0]
        
#         if not first_byte:
#             self.main_receive_buffer += data[1:]
#             return
            
#         first_byte -=1 
        
#         is_error = first_byte >0
        
#         if is_error:
#             # Colorize
#             if len(self.main_receive_buffer) > 0:
#                 self.terminal_write(f"\033[91mError: {self.main_receive_buffer.decode()}\033[0m\n")
#             else:
#                 self.terminal_write(f"\033[91mError\033[0m\n")
#         else:
#             if len(self.main_receive_buffer) > 0:        
#                 self.terminal_write(f"{self.main_receive_buffer.decode()}\n")
#             else:
#                 self.terminal_write(f"\033[92mOK\033[0m\n")
#         self.main_receive_buffer = b""    
        
#     def receive_aux(self, data):
#         self.terminal_write(f"{data.decode()}")
        
#     def terminal_write(self, text):
#         print(text, end="")
        
#         # Smehow this is needed to make the terminal work
#         with self.terminal.location(x=0, y=0):
#             pass
            
                    
#     def run(self):
#         self.transmit_thread_handle.start()
#         self.terminal = Terminal()

#         print( self.terminal.clear)
#         self.eros.transmit_packet(self.main_channel, "\n")
         
#         with self.terminal.location(x=0, y=0):
#             print(self.terminal.black_on_darkkhaki(self.terminal.center('EROS Terminal')))
                    
#         with self.terminal.cbreak(): #), self.terminal.hidden_cursor()
#             while True:

#                 # Read a character from the terminal
#                 inp = self.terminal.inkey()         
#                 #Send the character to the main channel     
#                 # self.main_transmit_buffer += inp.encode()  
#                 self.main_transmit_queue.put(inp.encode())
  
