import logging
from enum import Enum
import time

class TransportStates(Enum):
    IDLE = 0            # Idle state, not yet initialized
    CONNECTING = 1      # Connecting state, not yet connected
    CONNECTED = 2       # Connected state, all is good
    DISCONNECTED = 3    # Disconnected state, connection was lost
    DEAD = 4            # Permanent death state

class ErosTransport():
    framing = True
    verification = True
    name = "Generic Transport"
    
    def __init__(self, log_level = logging.INFO):
        self.log = logging.getLogger(self.name)
        self.log.setLevel(log_level)
        self.prev_state = TransportStates.IDLE
        self.state = TransportStates.IDLE
        self.status_callback = None
        
    def write(self, data: bytes) -> None:
        pass
    
    def read(self) -> bytes:
        pass

    def get_state(self) -> TransportStates:
        return self.state
    
    def wait_for_state(self, state:TransportStates, timeout:int) -> bool:
        start_time = time.time()
        while self.state != state:
            time.sleep(0.5)
            if time.time() - start_time > timeout:
                return False
        return True
    
            
    def attach_status_change_callback(self, callback: callable) -> None:
        """Attach a callback for when the status changes

        Args:
            callback (callable): Callback
        """
        self.status_callback = callback
        
    def close(self):
        pass     