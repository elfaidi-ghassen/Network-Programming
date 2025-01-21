from socket import *
server_name = "172.27.206.105" # can be an ip, or a hostname, i.e. www.website.com
# if you use a hostname, DNS lookup will be automatically made to get the ip.
server_port = 12000

client_socket = socket(AF_INET, SOCK_DGRAM)
# AF_INET -> we use IPv4, as an adress family the underlying network uses
# SOCK_DGRAM -> UDP
# we are not specifying port number of the socket, we let the OS do it for us.

message = input("input a sentence in lowercase: ")
client_socket.sendto(message.encode(), (server_name, server_port))
# message.encode() =>  it converts the string object to python's byte object
# the senders's IP and Port are also attached with the message, implicitely

modified_message, server_address = client_socket.recvfrom(2048)
# server_address contains both IP and Port of the server that sended the response
# we don't actually need that information, we already have it
# 2048 is the buffer size

print(modified_message.decode())
client_socket.close()
