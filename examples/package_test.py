from eros import Eros, ErosTCP
import logging

drv = ErosTCP(ip="10.250.100.108",port=6666,log_level=logging.ERROR)
eros = Eros(drv, log_level=logging.ERROR)


