from .drv_generic import ErosTransport,TransportStates
import socket
from enum import Enum

class ErosTCP(ErosTransport):
    framing = True
    verification = True
    name = "TCP"
    
    def __init__(self, ip:str, port:int, timeout = 3, auto_reconnect:bool = True,**kwargs) -> None:
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.sock = None
            
    def read(self) -> bytes:
        """ Read from the socket
        
        Returns:
            bytes: Data read from the socket
        """
        
        # Update the statemachine
        self.update_state()
        
        # If we are not connected, return
        if not self.state == TransportStates.CONNECTED:
            return None
         
        try:
            # Try to read from socket
            return self.sock.recv(1024)
        except socket.timeout:
            self.log.error(f"Socket[{self.sock.fileno()}] Timeout error, closing socket")
            self.state = TransportStates.DISCONNECTED
            return None
        
        except OSError: #Called when peer is reset
            
            # Only log if socket is expected to be alive
            self.log.error(f"Socket[{self.sock.fileno()}] closed unexpectedly (OSError)")
            self.state = TransportStates.DISCONNECTED
            return None
        
        except ConnectionAbortedError:
            self.log.error(f"Socket {self.sock.fileno()} closed unexpectedly ConnectionAbortedError")
            self.state = TransportStates.DISCONNECTED
            return None

    def write(self, data):
        """ Write to the socket, this call will not block
        
        Args:
            data (bytes): Data to write to the socket
        """
        
        # Check if we are connected
        if not self.state == TransportStates.CONNECTED:
            return False
        
        # Send data
        self.sock.send(data)
        
        return True
        
    def update_state(self):
        if self.state == TransportStates.IDLE:  
            # If in idle state, try to connect
            self.state = TransportStates.CONNECTING
            
        elif self.state == TransportStates.CONNECTING:
            # Try to connect
            if(self.connect()):
                self.state = TransportStates.CONNECTED
            else:
                self.state = TransportStates.DISCONNECTED

        elif self.state == TransportStates.CONNECTED:
            # Do nothing, we are connected
            pass
    
        elif self.state == TransportStates.DISCONNECTED:
            # Close the socket
            self.sock.close()

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
            
        
    def connect(self) -> bool:
        # Create and connect socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
            self.sock.settimeout(self.timeout)
            self.log.info(f"Conneting to {self.ip}:{self.port}")
            self.sock.connect((self.ip, self.port))
            
                        
        except Exception as e:
            self.log.error(f"socket [{self.sock.fileno()}] failed to connect with error: {e}")
            
            # Close the socket
            self.sock.close()
            return False
        
        self.log.info(f"Successfully connected")
        
        return True
    
    def close(self):
        self.log.info(f"Closing socket: {self.sock.fileno()}")
        self.state = TransportStates.DEAD
        self.sock.close()
    