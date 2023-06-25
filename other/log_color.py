import multiprocessing as mp
import logging 
import time
import colorlog

def setup_logger():
    # Create a logger object.
    logger = logging.getLogger()
    
    # Set the level of logger. It could be DEBUG, INFO, WARNING, ERROR, CRITICAL.
    logger.setLevel(logging.DEBUG)

    # Set up colored logging. The "%(log_color)s" specifies where to color the message.
    log_colors = {
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }

    # Create a formatter object
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s[%(name)-12s]%(reset)s %(message)s",
        datefmt=None,
        reset=True,
        log_colors=log_colors,
        secondary_log_colors={},
        style='%'
    )

    # Add formatter to the handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Add handler to the logger
    logger.addHandler(stream_handler)

    return logger
