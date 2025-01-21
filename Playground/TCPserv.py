from socket import *
server = "192.168.1.22"
port = 12003
welcome_socket = socket(AF_INET, SOCK_STREAM)
welcome_socket.bind((server, port))

welcome_socket.listen(1)
print("the server is running")
while True:
    connection_socket, client_adress = welcome_socket.accept()
    print("a TCP connection with", client_adress, "was created")
    n1 = connection_socket.recv(1024)
    n2 = connection_socket.recv(1024)
    result = sum(map(lambda n : int(n.decode()),[n1, n2]))
    connection_socket.send(str(result).encode())
    connection_socket.close()

