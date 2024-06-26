from eros_core import Eros, ErosSerial, TransportStates
import time
import logging
import coloredlogs, logging

# Setup logging
import pytest

from eros_core import Eros
import time


IP = "10.250.100.224"
PORT = 6767


@pytest.fixture(autouse=True)
def log():
    log = logging.getLogger("TEST")
    yield log


def test_eros_tcp_open_close(log):
    for i in range(10):
        log.info(f"Test iteration {i}")
        drv = ErosSerial(log_level=logging.INFO, auto_reconnect=True)
        eros = Eros(drv, log_level=logging.WARNING)
        # Wait until the connection is established
        assert eros.wait_for_state(TransportStates.CONNECTED, 10)

        eros.transmit_packet(1, f"Some test data, iteration {i}")
        eros.close()

        # Wait until the the driver is closed
        assert eros.wait_for_state(TransportStates.DEAD, 2)
        assert drv.get_state() == TransportStates.DEAD


def test_ros_tcp_troughput(log):
    for u in range(3):
        # setup_logging()
        # Initialize the driver
        drv = ErosSerial(log_level=logging.INFO, auto_reconnect=True)

        # Initialize the Eros core
        eros = Eros(drv, log_level=logging.WARNING)

        # Wait until the connection is established
        assert eros.wait_for_state(TransportStates.CONNECTED, 2)
        # Send some data
        for i in range(200):
            for channel in [1, 2, 3, 4]:
                log.info(f"Sending data on channel {channel}")
                eros.transmit_packet(channel, f"Some test data, iteration {i}")
            time.sleep(0.01)

        time.sleep(3)

        # Close the driver
        eros.close()
        # Wait until the the driver is closed
        assert eros.wait_for_state(TransportStates.DEAD, 2)
        assert drv.get_state() == TransportStates.DEAD


if __name__ == "__main__":
    log = logging.getLogger("TEST")
    # Set log level
    coloredlogs.install(level="DEBUG")

    # test_eros_tcp_open_close(log)
    test_ros_tcp_troughput(log)
