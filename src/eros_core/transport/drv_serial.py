import serial
from .drv_generic import ErosTransport, TransportStates
from typing import List
from dataclasses import dataclass
from serial.tools import list_ports
import time
import sys

VID = 4292  # ESP32 UART VID


class ErosSerial(ErosTransport):
    framing = True
    verification = True
    serial_handle = None

    @dataclass
    class serial_port_info:
        """Dataclass to store serial port information"""

        port: str
        description: str
        pid: str
        vid: str
        serial_number: str

    def __init__(
        self, port=None, baudrate=None, auto_reconnect=True, vid=VID, **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.auto_reconnect = auto_reconnect

        # Autodetect port if not specified
        if port is None or port == "auto":
            ports = ErosSerial.get_serial_ports(vid=vid)
            if len(ports) == 0:
                raise IOError("No serial ports found")
            port = ports[0].port

        if baudrate is None:
            baudrate = 2000000
        self.port = port
        self.baudrate = baudrate

    def read(self) -> bytes:
        """Read data from the serial port

        Returns:
            bytes: Data read from the serial port
        """
        # Update the statemachine
        self.update_state()

        # If we are not connected, return
        if not self.state == TransportStates.CONNECTED:
            return None
        try:
            if self.serial_handle.in_waiting > 0:
                data = self.serial_handle.read_all()
            else:
                data = self.serial_handle.read(1)

        except Exception as e:
            self.log.error(f"Failed to read: {e}")
            self.state = TransportStates.DISCONNECTED
            return None

        self.log.debug(f"Received: {data}")

        return data

    def write(self, data: bytes):
        """Write data to the serial port

        Args:
            data (bytes): Data to write
        """

        # Check if we are connected
        if not self.state == TransportStates.CONNECTED:
            return False

        self.log.debug(f"Transmitting: {data}")
        self.serial_handle.write(data)

    def connect(self) -> bool:
        try:
            # Open serial port
            self.serial_handle = serial.Serial(self.port,
                                            baudrate=self.baudrate,
                                            timeout=None,
                                            write_timeout=0,
                                            rtscts=False,
                                            dsrdtr=False,
                                            xonxoff=False)
            
            # Increase buffer size if in windows
            if sys.platform == "win32":
                self.serial_handle.set_buffer_size(
                    rx_size=1024 * 1024, tx_size=1024 * 1024
                )
            else:
                # TODO: Find a way to increase buffer size in linux
                pass

        except Exception as e:
            self.log.error(f"Failed to connect: {e}")
            time.sleep(2)
            return False

        self.log.info("Successfully connected")
        return True

    def update_state(self):
        if self.state == TransportStates.IDLE:
            # If in idle state, try to connect
            self.state = TransportStates.CONNECTING

        elif self.state == TransportStates.CONNECTING:
            # Try to connect
            if self.connect():
                self.state = TransportStates.CONNECTED
            else:
                self.state = TransportStates.DISCONNECTED

        elif self.state == TransportStates.CONNECTED:
            # Do nothing, we are connected
            pass

        elif self.state == TransportStates.DISCONNECTED:
            if self.serial_handle is not None:
                # Close the socket
                self.serial_handle.close()
                self.serial_handle = None

            # Try to reconnect
            if self.auto_reconnect:
                self.state = TransportStates.CONNECTING
            else:
                self.state = TransportStates.DEAD

        elif self.state == TransportStates.DEAD:
            # Do nothing, we are dead
            pass

        if self.prev_state != self.state:
            self.log.debug(f"State changed from {self.prev_state} to {self.state}")
            self.prev_state = self.state
            if self.status_callback is not None:
                self.status_callback(self.state)

    def close(self):
        self.log.info("Closing serial port")
        self.state = TransportStates.DEAD
        if self.serial_handle is not None:
            self.serial_handle.close()
            self.serial_handle = None

    def get_serial_ports(pid: str = None, vid: str = None) -> List[serial_port_info]:
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

            discovered_ports.append(
                ErosSerial.serial_port_info(
                    port.device,
                    port.description,
                    port.pid,
                    port.vid,
                    port.serial_number,
                )
            )
        return discovered_ports
