import multiprocessing as mp
from packeteiser import COBS_PACKETIZER
import logging 
import time
import colorlog

from RSP import RSP
import log_color

# Create a logger
logger = log_color.setup_logger()

# Create the virtual pipe
master_pipe, child_pipe = mp.Pipe()
        
# init logging
master = COBS_PACKETIZER("master",master_pipe, logging.ERROR)
child = COBS_PACKETIZER("child",  child_pipe, logging.ERROR)

master_rsp = RSP("master_RSP", master, logging.ERROR)
child_rsp = RSP("child_RSP", child, logging.ERROR)


log = logging.getLogger("main")

for i in range(10):

    ret = master_rsp.send_packet(f"Hello World {i}".encode(), True)
    ret = child_rsp.send_packet(f"DATATAT {i}".encode(), True)
    
    if not ret.ok:
        log.error(f"Error: {ret.data}")
    else:
        log.info(f"Response: {ret.data}")

    

time.sleep(0.2)