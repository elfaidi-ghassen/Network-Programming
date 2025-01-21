from socket import *
server_port = 12001
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(("", server_port))


server_socket.listen(1)

print("...the server is ready to receive...")

words = {"Hello": "Bonjour", "Morning":"Matin", "Tree":"Arbre"}


while True:
    connection_socket, adr = server_socket.accept()
    english_word = connection_socket.recv(1024).decode()
    print(english_word)
    if english_word in words:
        message = words[english_word]
    else:
        message = "Word not found!"
    connection_socket.send(message.encode())
    connection_socket.close()
