from .drv_generic import ErosTransport, TransportStates
import socket


class ErosUDP(ErosTransport):
    framing = True
    verification = True

    def __init__(
        self, ip: str, port: int, auto_reconnect: bool = True, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.port))
        self.state = TransportStates.CONNECTED

        # Write sume dummy data to the socket to register ourselfs
        self.sock.sendto(b"connect", (self.ip, self.port))

    def read(self) -> bytes:
        self.log.debug(f"Listening on {self.ip}:{self.port}")
        try:
            data, addr = self.sock.recvfrom(1024)  # read data from the socket

        except OSError:
            return None

        self.log.debug(f"Received: {data}")
        return data

    def write(self, data: bytes):
        self.log.debug(f"Transmitting: {data}")
        self.sock.sendto(data, (self.ip, self.port))

    def close(self):
        self.log.info(f"Closing socket: {self.sock.fileno()}")
        self.sock.close()
        self.state = TransportStates.DEAD
