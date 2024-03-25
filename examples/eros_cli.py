from eros import ErosStream, ErosPacket
from typing import Union, Tuple
from queue import Queue
from enum import Enum
import threading

print_lock = threading.Lock()


class PacketType(Enum):
    DATA = 0
    END_OK = 1
    END_ERROR = 2

    def to_byte(self):
        return self.value.to_bytes(1, byteorder="big")


# Eros commandline
# - Send error messages over the serial port
# - Acknowledgement
# - Provide command tab autocomplete
# - Command history
# - help


class ErosCommandLineClient:
    def __init__(self, eros: Union[ErosStream, ErosPacket], channel: int) -> None:
        self.eros = eros
        self.channel = channel
        self.receive_queue = Queue()

        self.eros.attach_channel_callback(self.channel, self.receive_callback)

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
            buffer += data[1:]

            packet_type = PacketType(data[0])

            if packet_type == PacketType.END_OK or packet_type == PacketType.END_ERROR:
                break

        return packet_type, buffer

    def send(self, data: str) -> str:
        """Send a command to the device

        Args:
            data (str): Command to send

        Returns:
            str: Response
        """

        # Clear the queue
        self.flush_receive_queue()

        # Transmit the data
        self.eros.transmit(self.channel, data.encode())

        # Wait for response to be received on the receive callback
        packet_type, data = self.receive_transmission()

        if packet_type == PacketType.END_ERROR:
            return f"Error: {data.decode()}"
            # raise Exception(f"Error: {data}")

        elif packet_type == PacketType.END_OK:
            return data.decode()

    def send_debug(self, data: str) -> str:
        print(f"CLI: TX: '{data:16s}'  -> RX: '{self.send(data):16s}'")


class ErosCommandLineHost:
    class ErosCommandLineContext:
        def __init__(self, eros: Union[ErosStream, ErosPacket], channel: int) -> None:
            self.eros = eros
            self.channel = channel

        def transmit_data(self, data: str) -> None:
            packet_type = PacketType.DATA

            data = packet_type.to_byte() + data.encode()
            self.eros.transmit(self.channel, data)

        def transmit_type(self, packet_type: PacketType) -> None:
            self.eros.transmit(self.channel, packet_type.to_byte())

    def __init__(self, eros: Union[ErosStream, ErosPacket], channel: int) -> None:
        self.commands = {}

        eros.attach_channel_callback(channel, self.new_data)

        self.channel = channel
        self.eros = eros
        self.context = self.ErosCommandLineContext(eros, channel)

    def new_data(self, data: bytes) -> None:
        self.parse(data.decode())

    def register_command(self, command: str, callback: callable) -> None:
        self.commands[command] = callback

    def parse(self, command: str) -> None:
        command = command.strip()

        # Get first part of command
        args = command.split(" ")

        if len(args) == 0:
            print("No command")
            return

        callback = self.commands.get(args[0], None)

        if callback is None:
            print(f"Command '{args[0]}' not found")
            return

        ret = callback(args[1:], self.context)

        self.context.transmit_type(ret)
