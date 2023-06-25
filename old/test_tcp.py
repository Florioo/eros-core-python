import socket
import time

# Connect to a TCP socket
ip = "10.250.100.108"
port = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((ip, port))
for i in range(50):
    strign = "Hello World " + str(i)
    sock.send(strign.encode())
time.sleep(1)