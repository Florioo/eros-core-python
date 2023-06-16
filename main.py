import multiprocessing as mp
from packeteiser import framing
import logging 
import time
import colorlog
from stream_simulator import SerialSimulator
from RSP import PacketEncapsulation, RSPResponse
import log_color
import random

# Create a logger
logger = log_color.setup_logger()

# Create the virtual pipe
loge =  logging.ERROR
        
def child_data_handler(data: bytes):
    logger.info(f"Master received: {data}")

    if random.randint(0,10) < 5:
        return RSPResponse(False, "A Custom error ".encode())
    
    return RSPResponse(True, "OK".encode())
    
master_rsp = PacketEncapsulation("master_RSP", framing("master",SerialSimulator("COM1", 0), loge), loge)
child_rsp = PacketEncapsulation("child_RSP", framing("child",  SerialSimulator("COM1", 1), loge), loge)

child_rsp.add_packet_handler(child_data_handler)

log = logging.getLogger("main")

for i in range(100):

    ret = master_rsp.send_packet(f"DATATAT {i}".encode(), False)
    ret = master_rsp.send_packet(f"Hello World {i}".encode(), True)
    
    if not ret.ok:
        log.error(f"Error: {ret.data}")
    else:
        log.info(f"Response: {ret.data}")

    

time.sleep(0.2)




# # Ideal interface prototype


# serial_port = SerialSimulator("COM1", 0)
# Eros(serial_port)

# COBS_encoder = framing("COBS_encoder", serial_port)
# rsp = PacketEncapsulation("master_RSP", COBS_encoder)

# rsp.add_packet_handler(child_data_handler)
