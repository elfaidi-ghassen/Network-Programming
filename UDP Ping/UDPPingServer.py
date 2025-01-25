import random
from socket import *
import time

server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(("", 8220))
print("running")
while True:
    rand = random.randint(0, 10)
    message, address = server_socket.recvfrom(1024)
    message = message.upper()
    
    # The server simulates packet loss
    # 30% of packets will be lost
    if rand < 4:
        continue
    time.sleep(random.random() * 2) # simulate delay
    server_socket.sendto(message, address)
