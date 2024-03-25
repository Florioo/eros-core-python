from .drv_generic import ErosTransport, TransportStates
from queue import Queue


class ErosLoopback(ErosTransport):
    framing = True
    verification = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = Queue(maxsize=1000)
        self.state = TransportStates.CONNECTED

    def write(self, data: bytes) -> None:
        self.log.debug(f"Transmitting: {data}")
        self.queue.put(data)

    def read(self) -> bytes:
        data = self.queue.get()
        self.log.debug(f"Received: {data}")
        return data
