import time
from eros import ErosStream, ErosPacket
               
import eros_transport_serial_sim
import eros_transport_udp_sim

import threading
lock = threading.Lock()

def tracing_handler(data, ):
    with lock:
        print(f"Received {data}")
    

class channels:
    CHANNEL1 = 1
    
serial_loopback = eros_transport_serial_sim.ErosSerialSim("test",        eros_transport_serial_sim.ChannelType.LOOPBACK)
udp_loopback = eros_transport_udp_sim.ErosUDPSim("test", eros_transport_udp_sim.ChannelType.LOOPBACK)

eros_serial = ErosStream(serial_loopback)
eros_udp = ErosPacket(udp_loopback)


eros_serial.attach_channel_callback(channels.CHANNEL1, tracing_handler)
eros_udp.attach_channel_callback(channels.CHANNEL1, tracing_handler)

eros_serial.transmit(channels.CHANNEL1, b"test")
eros_serial.transmit(channels.CHANNEL1, b"testq")
eros_serial.transmit(channels.CHANNEL1, b"testr")
eros_udp.transmit(channels.CHANNEL1, b"test UDP")
eros_udp.transmit(channels.CHANNEL1, b"test UDP 1523")

time.sleep(1)

