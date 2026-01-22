from socket import *
from datetime import timezone, datetime
import mimetypes
import os
import traceback
from threadpool import ThreadPool 
from log import Log
from counter import Counter
import argparse



class HTTPServer:
    def __init__(self, port=8080, pending_queue_size=5):
        self.address = ("", port)
        self.pending_queue_size = pending_queue_size
        self.logs = Log("logs.txt")
        self.active_connections_counter = Counter()
    def __create_response_headers(self, status_line, mime_type, content_length):
        current_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %X UTC")
        headers = [
            status_line,
            "Date: " + current_date,
            "Server: Ghassen's laptop",
            "Connection: close",
            "Content-Type: " + mime_type + "",
            "Content-Length: " + str(content_length)
        ]
        
        return "\r\n".join(headers) + "\r\n\r\n"
    
    def __process_request(self, params):
        connection_socket, client_addr = params
        
        self.active_connections_counter.increment()
        print(f"Active Connections: {self.active_connections_counter.get_value():03}", end="\r")
        current_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %X UTC")
        text_mime = ["text/html", "text/css", "text/javascript"]
        image_mime = ["image/png", "image/jpeg"]

        try:
            message = connection_socket.recv(1024).decode().split("\r\n")
            request_line = message[0]
            method = request_line.split()[0]
            filename = request_line.split()[1]
            if filename == "/":
                filename = "."
            filename = filename.lstrip("/")
            if os.path.isdir(filename):
                status_line = "HTTP/1.1 200 OK"
                mime_type = "text/html"
                content = "<ul style='list-style:none'>"
                dirs = os.listdir(filename)
                
                for element in dirs:
                    if filename == ".":
                        content += f"<li><a href='{element}'>{element}</a></li>"
                    else:
                        content += f"<li><a href='{filename + "/" + element}'>{element}</a></li>"
                        
                content += "</ul>"
            else:
                
                mime_type = mimetypes.guess_type(filename)[0]
                if mime_type in text_mime:
                    content, status_line  = self.__get_file_content(filename, "r")
                elif mime_type in image_mime:
                    content, status_line  = self.__get_file_content(filename, "rb")
                else:
                    content = "<p>This file type is not supported</p>"
                    status_line = "HTTP/1.1 415 Unsupported Media Type"
                    mime_type = "text/html"
                if status_line == "HTTP/1.1 404 not found":
                    mime_type = "text/html"
                
            
            match method:
                case "GET":
                    output_headers = self.__create_response_headers(status_line, mime_type, len(content))
                    connection_socket.send(output_headers.encode())
                    if mime_type in image_mime:
                        connection_socket.send(content)
                    else:
                        connection_socket.send(content.encode())
                    connection_socket.send("\r\n".encode())
                case "HEAD":
                    output_headers = self.__create_response_headers(status_line, mime_type, len(content))
                    connection_socket.send(output_headers.encode())
                case default:
                    output_headers = "".join([
                        "HTTP/1.1 405 Method Not Allowed" + "\r\n",
                        "Date: " + current_date + "\r\n",
                        "Server: Ghassen's laptop" + "\r\n",
                        "Allow: GET, HEAD\r\n\r\n"
                    ])
                    connection_socket.send(output_headers.encode())

            connection_socket.close()
            self.logs.add_line(request_line, status_line, current_date, client_addr)
        
        except Exception as e:
            output_headers = "".join([
                "HTTP/1.1 500 Internal Server Error" + "\r\n",
                "Date: " + current_date + "\r\n",
                "Server: Ghassen's laptop\r\n\r\n",
                str(traceback.format_exc()),
                "\r\n"])
            connection_socket.send(output_headers.encode())
            self.logs.add_error(str(e) , current_date)
            connection_socket.close()


        self.active_connections_counter.decrement()
        print(f"Active Connections: {self.active_connections_counter.get_value():03}", end="\r")

    def __get_file_content(self, filename, mode):
            try:
                with open(filename, mode) as requested_file:
                    content = requested_file.read()
                return content, "HTTP/1.1 200 OK"
            except FileNotFoundError as e:
                with open("404.html") as file:
                    content = file.read()    
                return content, "HTTP/1.1 404 not found"




    def start(self):
        # create a TCP "welcoming" socket
        server_socket = socket(AF_INET, SOCK_STREAM)
        # bind the the server address
        server_socket.bind(self.address)
        server_socket.listen(self.pending_queue_size)
        
        max_pool_workers = 10
        max_queue_size = 50
        thread_pool = ThreadPool(self.__process_request, max_pool_workers, max_queue_size)
        print("...the server is ready...")
        
        while True:
            connection_socket, addr = server_socket.accept()
            thread_pool.add_task((connection_socket, addr))


parser = argparse.ArgumentParser(description="HTTP Server")
parser.add_argument("--port", type=int, default=8080, help="Port number (default: 8080)")
args = parser.parse_args()


web_server = HTTPServer(args.port)
web_server.start()