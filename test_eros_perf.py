
from eros_transport_serial import ErosSerial
from eros_transport_loopback import ErosLoopback
from eros import Eros
import time
import logging
from queue import Queue
# Setup logging
logging.basicConfig(level=logging.DEBUG)
import pytest
    
class RequestResponse():
    def __init__(self, eros: Eros, channel: int) -> None:
        self.eros = eros
        self.channel = channel
        self.receive_queue = Queue()
        self.eros.attach_channel_callback(self.channel, self.receive_callback)

    def receive_callback(self, data: str) -> str:
        self.receive_queue.put(data)
    
    def flush_receive_queue(self) -> None:
        while not self.receive_queue.empty():
            self.receive_queue.get()
    
    def send(self, data: str) -> str:
        self.flush_receive_queue()
        self.eros.transmit_packet(self.channel, data.encode())
        rx_data = self.receive_queue.get(timeout=1)
        print(f"TX: {data}  -> RX: {rx_data}")
        assert rx_data == data.encode()
    
def test_eros_serial_perf(benchmark):
    drv = ErosSerial(log_level=logging.ERROR)
    eros = Eros(drv, log_level=logging.ERROR)
    resp  = RequestResponse(eros, 5)
    benchmark(resp.send, "Hello World")
    
def test_eros_loopback_perf(benchmark):
    drv = ErosLoopback(log_level=logging.ERROR)
    eros = Eros(drv, log_level=logging.ERROR)
    resp  = RequestResponse(eros, 5)
    benchmark(resp.send, "Hello World")
