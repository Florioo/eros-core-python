import zmq
from .drv_generic import ErosTransport, TransportStates


class ErosZMQ(ErosTransport):
    framing = False
    verification = False

    def __init__(self, port=None, **kwargs) -> None:
        super().__init__(**kwargs)

        self.state = TransportStates.CONNECTED

        self.context = zmq.Context()
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://127.0.0.1:{port}")
        self.sub_socket.subscribe("")

        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.connect(f"tcp://127.0.0.1:{port+1}")

    def read(self) -> bytes:
        """Read data from the serial port

        Returns:
            bytes: Data read from the serial port
        """
        data = self.sub_socket.recv()
        return data

    def write(self, data: bytes):
        """Write data to the serial port

        Args:
            data (bytes): Data to write
        """
        self.pub_socket.send(data)
