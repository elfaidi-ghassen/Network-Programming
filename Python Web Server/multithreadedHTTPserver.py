from socket import *
from datetime import timezone, datetime
import mimetypes
import threading
import os
import traceback


class ThreadPool:
    def __init__(self, fn, MAX_WORKERS, QUEUE_SIZE):
        self.MAX_WORKERS = MAX_WORKERS
        self.QUEUE_SIZE = QUEUE_SIZE
        self.fn = fn
        
        self.full = threading.Semaphore(0)
        self.empty = threading.Semaphore(QUEUE_SIZE)
        self.mutex = threading.Semaphore(1)
        self.tasks_queue = []
        
        self.workers = [threading.Thread(target=self.__worker) for _ in range(MAX_WORKERS)]
        for thread in self.workers:
            thread.start()


    def __worker(self):
        while True:
            self.full.acquire()
            try:
                with self.mutex:
                    task = self.tasks_queue.pop(0)
                    self.fn(task)
            finally:
                self.empty.release()
    
    def add_task(self, task):
        self.empty.acquire()
        with self.mutex:
            self.tasks_queue.append(task)
        self.full.release()
class Log:
    def __init__(self, filename):
        self.filename = filename
        self.mutex = threading.Lock()

    def add_line(self, request_line, status_line, date, client_addr):
        self.mutex.acquire()
        with open(self.filename, "a") as file:
            file.write(f"REQUEST({client_addr[0]}): {request_line} -> RESPONSE: {status_line} : {date}\n")
        self.mutex.release()

    def add_error(self, exception_desc, date):
        self.mutex.acquire()
        with open(self.filename, "a") as file:
            file.write(f"{exception_desc} : {date}\n")
        self.mutex.release()

# A simple thread safe couter
class Counter:
    def __init__(self, value=0):
        self.value = value
        self.lock = threading.Lock()
    def increment(self):
        with self.lock:
            self.value += 1
    def decrement(self):
        with self.lock:
            self.value -= 1

    def get_value(self):
        with self.lock:
            return self.value

class HTTPServer:
    def __init__(self, adress=("", 8080), pending_queue_size=5):
        self.address = adress
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
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(self.address)
        server_socket.listen(self.pending_queue_size)
        max_pool_workers = 10
        max_queue_size = 50
        thread_pool = ThreadPool(self.__process_request, max_pool_workers, max_queue_size)
        print("...the server is ready...")
        
        while True:
            connection_socket, addr = server_socket.accept()
            thread_pool.add_task((connection_socket, addr))


web_server = HTTPServer(pending_queue_size=5)
web_server.start()