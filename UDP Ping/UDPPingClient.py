from socket import *
import sys
from datetime import datetime

server_port =  8220
if len(sys.argv) < 2:
    print("ERROR: The ping program expects an IP address as its argument")
    sys.exit()

NB_PACKETS = 10

client_socket = socket(AF_INET, SOCK_DGRAM)
client_socket.settimeout(3)
# ping message format: Ping sequence_number time 
name = sys.argv[1]
count_received = 0
total_rtt = 0

for i in range(1, NB_PACKETS + 1):
    initial_time = datetime.now()
    message = f"Ping {i} {initial_time.strftime('%H:%M:%S')}"
    client_socket.sendto(message.encode(), (name, server_port))
    try:
        response, adr = client_socket.recvfrom(1024)
        count_received += 1
        after_response = datetime.now()
        delta_time = after_response - initial_time
        print(f"Reply for {response.decode()} :: RTT {delta_time.total_seconds():.3f}s")
        total_rtt += delta_time.total_seconds()
    except TimeoutError as exception:
        print(f"Request timed out")


print("Ping statistics:")
lost = NB_PACKETS - count_received
print(f"\tPackets: Sent = {NB_PACKETS}, Received = {count_received}, Lost = {lost} ({lost / NB_PACKETS * 100}% loss)")
print("Average RTT (Round Trip Time)")
avg_rtt = 0 if not count_received else total_rtt / count_received
print(f"\tAvg: {(avg_rtt):.3f}")


