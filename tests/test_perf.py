from eros_core import Eros, ErosLoopback
import time
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

import time


def test_eros_simple():
    drv = ErosLoopback(log_level=logging.DEBUG)
    eros = Eros(drv)
    start = time.time()

    n = 1000
    for i in range(n):
        eros.transmit_packet(1, "\0" * 2000)

    delta = time.time() - start

    print(f"{(n/delta)} packets per second")
    print(f"{(n/delta)/1e6} Mpackets per second")
    print(f"{(delta/n)*1e9} ns per packet")


drv = ErosLoopback(log_level=logging.DEBUG)
eros = Eros(drv)


def test_perf_pre(packet_size: int, test_time: float = 0.5):
    start = time.time()
    i = 0
    data = b"1" * packet_size
    while time.time() - start < test_time:
        i += 1
        eros.transmit_packet(1, data)

    delta = time.time() - start
    print(
        f"PRE [{packet_size:6}] {(i*packet_size/delta)/1e6:10.2f} MB/s  {i/delta:10.2f} packets/s  {(i/delta)/1e6:10.2f} Mpackets/s {(delta/i)*1e9:10.2f} ns/packet"
    )


if __name__ == "__main__":
    its = 6

    for i in range(1, its):
        test_perf_pre(10**i, 1)
