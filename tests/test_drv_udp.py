
from eros_core import Eros, ErosSerial, ErosLoopback,ErosUDP, TransportStates
import time
import logging
from queue import Queue
import coloredlogs, logging

# Setup logging
import pytest

import click
from eros_core import Eros, CLIResponse
import time


IP = "10.172.255.27"
PORT = 5555
import sys

@pytest.fixture(autouse=True)
def log():
    log = logging.getLogger("TEST")
    yield log


def test_eros_tcp_open_close(log):
    for i in range(10):
        log.info(f"Test iteration {i}")
        drv = ErosUDP(ip=IP, port=PORT,log_level=logging.INFO)
        eros = Eros(drv, log_level=logging.WARNING)
        # Wait until the connection is established
        assert(eros.wait_for_state(TransportStates.CONNECTED, 2))
        
        eros.transmit_packet(1, f"Some test data, iteration {i}")
        eros.close()
        
        # Wait until the the driver is closed
        assert(eros.wait_for_state(TransportStates.DEAD, 2))
        assert(drv.get_state() == TransportStates.DEAD)

def test_eros_receive_data():
    drv = ErosUDP(ip=IP, port=PORT,log_level=logging.INFO)
    start_time = time.time()
    duration = 10
    print(f"connected to {IP}:{PORT}")
    
    
    while time.time() - start_time < duration:
        print(drv.read())

def test_ros_tcp_troughput(log):
    for u in range(3):

        # Initialize the driver
        drv = ErosUDP(ip=IP, port=PORT,log_level=logging.INFO)
        
        # Initialize the Eros core 
        eros = Eros(drv, log_level=logging.WARNING)

        # Wait until the connection is established
        assert(eros.wait_for_state(TransportStates.CONNECTED, 2))
        
        # Send some data
        for i in range(200):
            for channel in [1,2,3,4]:
                log.info(f"Sending data on channel {channel}")
                eros.transmit_packet(channel, f"Some test data, iteration {i}")
            time.sleep(0.01)
            
        time.sleep(3)
        
        # Close the driver
        eros.close()
        # Wait until the the driver is closed
        assert(eros.wait_for_state(TransportStates.DEAD, 2))
        assert(drv.get_state() == TransportStates.DEAD)
        
if __name__ == "__main__":
    test_eros_receive_data()
