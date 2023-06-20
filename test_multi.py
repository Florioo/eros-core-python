import time
from eros import ErosStream, ErosPacket
import stream_simulator
from typing import Union, List
from queue import Queue
from enum import Enum
import threading

from eros_cli import ErosCommandLineClient, PacketType, ErosCommandLineHost

print_lock = threading.Lock()

class channels:
    CHANNEL1 = 1
    CHANNEL2 = 2
    
eros_host   = ErosStream(stream_simulator.SerialSimulator("test", stream_simulator.ChannelType.PART_A))
eros_device = ErosStream(stream_simulator.SerialSimulator("test", stream_simulator.ChannelType.PART_B))

cli = ErosCommandLineClient(eros_host, channels.CHANNEL2)
cli_host = ErosCommandLineHost(eros_device, channels.CHANNEL2)

data = {}

def ping(args: List[str], context:ErosCommandLineHost.ErosCommandLineContext):
    context.transmit_data("pong")
    return PacketType.END_OK

def get_value(args: List[str], context:ErosCommandLineHost.ErosCommandLineContext):
    if len(args) == 0:
        context.transmit_data("Missing argument")
        return PacketType.END_ERROR
    
    if args[0] not in data:
        context.transmit_data("Key not found")
        return PacketType.END_ERROR
    
    context.transmit_data(data[args[0]])
    return PacketType.END_OK

def set_value(args: List[str], context:ErosCommandLineHost.ErosCommandLineContext):
    if len(args) < 2:
        context.transmit_data("Missing argument")
        return PacketType.END_ERROR
    
    data[args[0]] = args[1]
    return PacketType.END_OK

cli_host.register_command("ping", ping)
cli_host.register_command("get", get_value)
cli_host.register_command("set", set_value)

def host_tracing_handler(data, ):
    with print_lock:
        print(f"TRACING Host received: {data}")

def device_tracing_task():
    i = 0
    while True:
        time.sleep(0.1)
        i += 1
        eros_device.transmit(channels.CHANNEL1, f"test{i}")
        if i >= 10:
            break
        
eros_host.attach_channel_callback(channels.CHANNEL1, host_tracing_handler)
# eros_device.attach_channel_callback(channels.CHANNEL2, device_cli_handler)


cli.send_debug("get test")
cli.send_debug("set test 10")
cli.send_debug("get test")
cli.send_debug("set test 10wq")
cli.send_debug("get test")

cli.send_debug("ping")
cli.send_debug("ping")
cli.send_debug("ping")
cli.send_debug("ping")

threading.Thread(target=device_tracing_task, daemon=True).start()

time.sleep(1)
eros_host.transmit(channels.CHANNEL2, b"ping")

time.sleep(1)

