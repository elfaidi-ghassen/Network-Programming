from socket import *

server_address = "192.168.1.12"
port = 8080
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(("", 8080))
server_socket.listen(5)
print("server is up and runnning")
while True:
    connection_socket, address = server_socket.accept()
    message = connection_socket.recv(1024)
    print(message.decode())
    connection_socket.close()
