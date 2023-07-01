import logging

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
