import serial    
from eros import ErosTransport
from typing import List
from dataclasses import dataclass
from serial.tools import list_ports

class ErosSerial(ErosTransport):
    framing = True
    verification = True
      
    @dataclass
    class serial_port_info:
        """Dataclass to store serial port information
        """
        port: str
        description: str
        pid: str
        vid: str
        serial_number: str
        
        
    def __init__(self, port=None,**kwargs) -> None:
        super().__init__(**kwargs)
        
        # Autodetect port if not specified
        if port is None:
            ports = ErosSerial.get_serial_ports(vid=4292)
            if len(ports) == 0:
                raise Exception("No serial ports found")
            port = ports[0].port

        # Open serial port
        self.serial_handle = serial.Serial(port,
                                           baudrate=1152000,
                                           timeout=None,
                                           write_timeout=1,
                                           rtscts=False,
                                           dsrdtr=True,
                                           xonxoff=True)
        
        # Increase buffer size
        self.serial_handle.set_buffer_size(rx_size = 1024*1024,
                                           tx_size = 1024*1024)
        self.log.debug(f"Opened serial port: {port}")
    def read(self) -> bytes:
        """Read data from the serial port

        Returns:
            bytes: Data read from the serial port
        """
        if self.serial_handle.in_waiting > 0:
            data = self.serial_handle.read_all()
        else:
            data = self.serial_handle.read(1)
        self.log.debug(f"Received: {data}")
        return data
    def write(self, data:bytes):
        """Write data to the serial port

        Args:
            data (bytes): Data to write
        """
        self.log.debug(f"Transmitting: {data}")
        self.serial_handle.write(data)
        
        

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

