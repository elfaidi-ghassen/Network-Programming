from socket import *
from datetime import timezone, datetime
import mimetypes

server_port = 8000
server_address = "192.168.43.110"

# create the welcoming TCP socket
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(("", server_port))
server_socket.listen()



def process_http_request(connection_socket):
    message = connection_socket.recv(1024).decode().split()
    if len(message) < 2: # at least two headers
        connection_socket.close()
        return

    methode = message[0]
    filename = message[1]
    version = message[2]
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %X GMT")
    
    try:
        # remove the "/" (e.g. "/index.html" -> "index.h")
        if len(filename) > 0:
            filename = filename[1:]
        
        if filename == "":
            filename = "index.html"
    
    
        mime = mimetypes.guess_type(filename)[0]
        if mime == "application/pdf":
            f = open(filename, "rb")
            content = f.read()
            
        else:
            f = open(filename, "r")
            content = f.read().encode()
            
        outputdata = version + " 200 OK\r\n"
        outputdata += "Date: " + date + "\r\n"
        outputdata += "Age: 0\r\n" 
        outputdata += "Server: Ghassen's HP laptop\r\n"
        outputdata += "Content-Type: " + mime +"\r\n"
        outputdata += "Content-Length: " + str(len(content)) + "\r\n\r\n"
        connection_socket.send(outputdata.encode())
        connection_socket.send(content)
        connection_socket.send("\r\n".encode())
    
    except FileNotFoundError:
        f = open("404.html")
        content = f.read()
        outputdata = version + " 404 not found\r\n"
        outputdata += "Date: " + date + "\r\n" 
        outputdata += "Age: 0\r\n"
        outputdata += "Server: Ghassen's HP laptop\r\n"
        outputdata += "Content-Type: " + mimetypes.guess_type(filename)[0] +"\r\n"
        outputdata += "Content-Length: " + str(len(content)) + "\r\n\r\n"
        outputdata += content +"\r\n"
        connection_socket.send(outputdata.encode())
    print("sent successfully")
    connection_socket.close()


while True:
    print("...the server is ready...")
    connection_socket, _ = server_socket.accept()
    process_http_request(connection_socket)
