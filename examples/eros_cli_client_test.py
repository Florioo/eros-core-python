

from eros_transport_udp import ErosUDP
from eros import ErosStream
from eros_transport_serial import ErosSerial
from eros_transport_tcp import ErosTCP
from eros_cli_client import ErosCommandLineClient
import time
from queue import Queue

tramsport = ErosTCP("10.250.100.108", 5555)

# def measure_round_trip_raw():
#     start = time.time()
#     tramsport.write(b"FLORIS")
#     tramsport.read()
#     end = time.time()
#     return (end-start)*1000

# # for i in range(100):
# #     print(f"RAW: {measure_round_trip_raw():6.2f} ms")
    
# q = Queue()
# eros.attach_channel_callback(1, lambda data: q.put(data))
eros = ErosStream(tramsport)


# def measure_round_trip_eros(eros:ErosStream, q:Queue):

#     start_time_t = time.time()
#     eros.transmit(1, b"5")
    
#     print(q.get(timeout=3))
#     end = time.time()
#     return (end-start_time_t)*1000

# for i in range(100):
#     print(f"EROS: {measure_round_trip_eros(eros,q):6.2f} ms")
    

# eros = ErosStream(ErosSerial())
# eros_serial.transmit(1, b"Hello World")
eros.attach_channel_callback(1, lambda data: print(data.decode(),end=""))

eros.transmit(2, b"Hello World")
eros.transmit(1, b"Hello World")

time.sleep(1)
cli = ErosCommandLineClient(eros,6)

sta = time.time()
for i in range(100):
    print(f"{1000*cli.ping():6.2f} ms")

print(f"Average frequency: {100/(time.time()-sta)} Hz")