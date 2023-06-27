from eros import Eros, ErosSerial
import time

serial = ErosSerial()
eros = Eros(serial)
eros.attach_channel_callback(1, lambda data: print(data.decode(),end=""))

# Sleep forever
while 1:
    time.sleep(1)