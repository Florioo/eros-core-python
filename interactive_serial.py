#!/usr/bin/env python3

import time
from eros import ErosStream, ErosPacket
import serial    
from typing import List
from dataclasses import dataclass
from serial.tools import list_ports
from eros_transport_serial import ErosSerial
from blessed import Terminal

class ErosInteractiveCLI():
    def __init__(self, eros:ErosStream, main_channel, aux_channel) -> None:
        self.eros = eros
        self.main_channel = main_channel
        self.aux_channel = aux_channel
    
        self.main_receive_buffer = b""
        
        self.eros.attach_channel_callback(self.main_channel, self.receive_main)
        self.eros.attach_channel_callback(self.aux_channel, self.receive_aux)
        self.terminal = Terminal()
        

    def receive_main(self, data):
        first_byte = data[0]
        
        if not first_byte:
            self.main_receive_buffer += data[1:]
            return
            
        first_byte -=1 
        
        is_error = first_byte >0
        
        if is_error:
            # Colorize
            if len(self.main_receive_buffer) > 0:
                self.terminal_write(f"\033[91mError: {self.main_receive_buffer.decode()}\033[0m\n")
            else:
                self.terminal_write(f"\033[91mError\033[0m\n")
        else:
            if len(self.main_receive_buffer) > 0:        
                self.terminal_write(f"{self.main_receive_buffer.decode()}\n")
            else:
                self.terminal_write(f"\033[92mOK\033[0m\n")
        self.main_receive_buffer = b""    
        
    def receive_aux(self, data):
        self.terminal_write(f"{data.decode()}")
        
    def terminal_write(self, text):
        print(text, end="")
        
        with self.terminal.location(x=0, y=0):
            print(self.terminal.black_on_darkkhaki(self.terminal.center('This is a bar')))
                    
    def run(self):
        self.terminal = Terminal()

        with self.terminal.cbreak(): #), self.terminal.hidden_cursor()
            while True:

                # Read a character from the terminal
                inp = self.terminal.inkey()         
                
                #Send the character to the main channel         
                self.eros.transmit(self.main_channel, inp.encode())
                
  
    
# eros_serial = ErosInteractiveCLI(ErosStream(ErosSerial()),6,7)
# eros_serial.run()


from eros_transport_udp import ErosUDP
from eros import ErosStream
from eros_transport_tcp import ErosTCP
import time
eros_serial = ErosStream(ErosTCP("10.250.100.108", 5555))
print("Connected")
eros_serial.transmit(1, b"Hello World")

cli = ErosInteractiveCLI(eros_serial,6,7)
cli.run()

# eros_serial.attach_channel_callback(1, lambda data: print("Got data: ", data))

# for i in range(0, 10):
#     eros_serial.transmit(1, b"Hello World")
