from socket import *
server_port = 12000
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(("", server_port))

print("the server is ready to receive")
while True:
    message, client_adress = server_socket.recvfrom(2048)
    print(message)
    modified_message = message.decode().upper()
    
    server_socket.sendto(modified_message.encode(), client_adress)
