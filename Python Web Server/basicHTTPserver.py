from socket import *
from datetime import timezone, datetime
import mimetypes
# import os
# import platform
# TODO: add the Last-Modified field

server_port = 1800
server_address = "192.168.1.22"

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(("", server_port))
server_socket.listen(1)

while True:
    print("...the server is ready...")
    connection_socket, address = server_socket.accept()
    message = connection_socket.recv(1024).decode().split()
    if len(message) < 2: # at least two headers
        connection_socket.close()
        continue

    filename = message[1]
    version = message[2]
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %X GMT")
    try:
        if filename != "":
            filename = filename[1:]
        if filename == "":
            filename = "index.html"
        
        extension = filename.split(".")[-1]
        
        f = open(filename, "r")
        content = f.read()
        outputdata = version + " 200 OK\r\n"
        outputdata += "Date: " + now + "\r\n"
        outputdata += "Age: 0\r\n" 
        outputdata += "Server: Ghassen's HP laptop\r\n"
        outputdata += "Content-Type: " + mimetypes.guess_type(filename)[0] +"\r\n"
        outputdata += "Content-Length: " + str(len(content)) + "\r\n\r\n"
        outputdata += content + "\r\n"
        connection_socket.send(outputdata.encode())
        
    
    except FileNotFoundError:
        f = open("404.html")
        content = f.read()
        outputdata = version + " 404 not found\r\n"
        outputdata += "Date: " + now + "\r\n" 
        outputdata += "Age: 0\r\n"
        outputdata += "Server: Ghassen's HP laptop\r\n"
        outputdata += "Content-Type: " + mimetypes.guess_type(filename)[0] +"\r\n"
        outputdata += "Content-Length: " + str(len(content)) + "\r\n\r\n"
        outputdata += content +"\r\n"
        connection_socket.send(outputdata.encode())

    connection_socket.close()
server_socket.close()
