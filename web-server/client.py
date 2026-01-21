from socket import *
import sys

# e.g. python client.py GET localhost 80 /index.html
mode = sys.argv[1]
server_address = sys.argv[2]
port = int(sys.argv[3])
filename = sys.argv[4]

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_address, port))

outputdata = (
    f"{mode} {filename} HTTP/1.1\r\n",
    f"Host: {server_address}\r\n",
    f"User-Agent: VSC (Very Simple Client)\r\n"
)
output_message = "".join(outputdata)
client_socket.send(output_message.encode())

response = b""
while True:
    data = client_socket.recv(1024)
    if not data:  # No more data
        break
    response += data
print(response.decode())

client_socket.close()