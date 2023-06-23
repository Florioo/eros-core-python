import socket
from eros_drv_udp import ErosUDP

from eros import ErosStream
import time
eros_serial = ErosStream(ErosUDP("10.250.100.108", 5555))
eros_serial.attach_channel_callback(1, lambda data: print("Got data: ", data))

for i in range(0, 10):
    eros_serial.transmit(1, b"Hello World")
