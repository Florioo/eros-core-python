
#!/usr/bin/env python3

import time
from eros import ErosStream, ErosPacket
import serial    
from typing import List
from dataclasses import dataclass

from serial.tools import list_ports

class ErosSerial():
    
    @dataclass
    class serial_port_info:
        """Dataclass to store serial port information
        """
        port: str
        description: str
        pid: str
        vid: str
        serial_number: str
        
        
    def __init__(self,port=None) -> None:
        if port is None:
            ports = ErosSerial.get_serial_ports(vid=4292)
            if len(ports) == 0:
                raise Exception("No serial ports found")
            port = ports[0].port
            
        self.ser = serial.Serial(port, baudrate=1152000,timeout=None, write_timeout = 1, rtscts=False, dsrdtr=True, xonxoff=True)
        # increase buffer size
        self.ser.set_buffer_size(rx_size = 1024*1024, tx_size = 1024*1024)
        

    def get_serial_ports(pid:str = None, vid:str = None) -> List[serial_port_info]:
        """Get a list of serial ports
        
        Args:
            pid (str, optional): Filter by product id. Defaults to None.
            vid (str, optional): Filter by vendor id. Defaults to None.
            
        Returns:
            List[serial_port_info]: List of serial ports
            
        """
        discovered_ports = []
        for port in list_ports.comports():
            
            # Check if the port should be filtered
            if pid is not None and port.pid != pid:
                continue
            
            if vid is not None and port.vid != vid:
                continue

            discovered_ports.append(ErosSerial.serial_port_info(port.device,
                                                    port.description,
                                                    port.pid,
                                                    port.vid,
                                                    port.serial_number))
        return discovered_ports


    def read(self):
    
        if self.ser.in_waiting > 0:
            return self.ser.read_all()
        else:
            return self.ser.read(1)
    
    def write(self, data):
        self.ser.write(data)
        
