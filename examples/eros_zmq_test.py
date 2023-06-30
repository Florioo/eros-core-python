

from eros import ErosZMQ, Eros

transport = ErosZMQ(2000)

eros = Eros(transport)

eros.attach_channel_callback(1, lambda data: print(data.decode(),end=""))
eros.spin()