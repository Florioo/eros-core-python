from eros import Eros, ErosSerial,ErosUDP,ErosTCP
import time
import click


def start_eros_log(transport, channel):
    eros = Eros(transport)
    eros.attach_channel_callback(channel, lambda data: print(data.decode(),end=""))
    
    while(1):
        time.sleep(1)

@click.group()
def eros_log():
    pass


@eros_log.command()
@click.argument('channel', type=int, default=1)
@click.option('--port', default=None, help='Port to use for UART communication')
@click.option('--baud', default=115200, help='Baud rate for UART communication')

def uart(channel, port, baud):
    click.echo(f"Running UART channel {channel} with port {port} and baud {baud}")
    start_eros_log(ErosSerial(port),channel)

        
@eros_log.command()
@click.argument('channel', type=int)
@click.option('--ip', default='192.168.0.1', help='IP address to use for UDP communication')
@click.option('--port', default=6666, help='Port to use for UDP communication')
def udp(channel, ip, port):
    click.echo(f"Running UDP channel {channel} with IP {ip} and port {port}")
    start_eros_log(ErosUDP(ip, port),channel)
    
@eros_log.command()
@click.argument('channel', type=int)
@click.option('--ip', default='192.168.0.1', help='IP address to use for TCP communication')
@click.option('--port', default=6666, help='Port to use for TCP communication')
def tcp(channel, ip, port):
    click.echo(f"Running TCP channel {channel} with IP {ip} and port {port}")
    start_eros_log(ErosTCP(ip, port),channel)

if __name__ == '__main__':
    eros_log()