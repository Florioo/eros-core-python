from eros import ErosStream
from typing import Tuple
from queue import Queue
from enum import Enum
import time


class PacketType(Enum):
    DATA = 0
    END_OK = 1
    END_ERROR = 2

    def to_byte(self):
        return self.value.to_bytes(1, byteorder="big")


class ErosCommandLineClient:
    def __init__(self, eros: ErosStream, channel: int) -> None:
        self.eros = eros
        self.channel = channel
        self.receive_queue = Queue()

        self.eros.attach_channel_callback(self.channel, self.receive_callback)
        self.timee = time.time()

    def receive_callback(self, data: str) -> str:
        self.receive_queue.put(data)

    def flush_receive_queue(self) -> None:
        while not self.receive_queue.empty():
            self.receive_queue.get()

    def receive_transmission(self, timeout: int = 1) -> Tuple[PacketType, bytearray]:
        """Receive a transmission from the receive queue

        Args:
            timeout (int, optional): Timeout in seconds. Defaults to 1.

        Returns:
            Tuple[PacketType, bytearray]: Packet type and data
        """

        buffer = b""
        while True:
            data = self.receive_queue.get(timeout=timeout)
            # self.print_lap(f"got {data}")

            buffer += data[1:]

            prefix = data[0]
            if prefix == 0:
                continue

            prefix -= 1

            if prefix == 0:
                return PacketType.END_OK, buffer
            else:
                return PacketType.END_ERROR, buffer

    def print_lap(self, strin):
        print(f"{strin}: {1000*(time.time()-self.timee)}ms")

    def send(self, data: str) -> str:
        """Send a command to the device

        Args:
            data (str): Command to send

        Returns:
            str: Response
        """

        # Clear the queue
        self.timee = time.time()

        self.flush_receive_queue()

        # self.print_lap("flush")
        data += "\n"
        # Transmit the data
        self.eros.transmit(self.channel, data.encode())
        # self.print_lap("transmit")

        # Wait for response to be received on the receive callback
        packet_type, data = self.receive_transmission()
        # self.print_lap("post_receive")

        return data

        # if packet_type == PacketType.END_ERROR:
        #     return f"Error: {data.decode()}"
        #     # raise Exception(f"Error: {data}")

        # elif packet_type == PacketType.END_OK:
        #     return data.decode()

    def send_debug(self, data: str) -> str:
        print(f"CLI: TX: '{data:16s} -> RX: '{self.send(data)}")

    def ping(self) -> float:
        """Ping the device

        Returns:
            float: Ping time in seconds
        """

        start = time.time()
        self.send("ping")
        end = time.time()
        return end - start
