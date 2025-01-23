from socket import *
from datetime import timezone, datetime
import mimetypes
import threading

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
                    task = self.tasks_queue.pop()
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

class HTTPServer:
    def __init__(self, adress=("", 80), pending_queue_size=5):
        self.address = adress
        self.pending_queue_size = pending_queue_size
        self.logs = Log("logs.txt")
        self.active_connections_counter = 0
        self.counter_lock = threading.Lock()
    def __create_response_headers(self, status_line, mime_type, content_length):
        current_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %X UTC")
        headers = [
            status_line,
            "Date: " + current_date,
            "Server: Ghassen's HP laptop",
            "Connection: close",
            "Content-Type: " + mime_type + "",
            "Content-Length: " + str(content_length)
        ]
        return "\r\n".join(headers) + "\r\n\r\n"
    
    def __process_request(self, params):
        connection_socket, client_addr = params
        
        self.counter_lock.acquire()
        self.active_connections_counter += 1
        print(f"Active Connections: {self.active_connections_counter:03}", end="\r")

        self.counter_lock.release()

        current_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %X UTC")
        
        try:
            message = connection_socket.recv(1024).decode().split("\r\n")
            
            request_line = message[0]
            if not message:
                connection_socket.close()
                return

            # e.g. GET /index.html HTTP/1.1
            filename = request_line.split()[1].lstrip("/")
            if not filename:
                filename = "index.html"
            with open(filename) as requested_file:
                content = requested_file.read()
            
            
            mime_type = mimetypes.guess_type(filename)[0]
            if not mime_type:
                connection_socket.close()
                return
            
            status_line = "HTTP/1.1 200 OK"
            output_headers = self.__create_response_headers(status_line, mime_type, len(content))

            connection_socket.send(output_headers.encode())
            connection_socket.send(content.encode())
            connection_socket.send("\r\n".encode())
            connection_socket.close()
            self.logs.add_line(request_line, status_line, current_date, client_addr)
        except FileNotFoundError as e:

            with open("404.html") as file:
                content = file.read()
    
            status_line = "HTTP/1.1 404 not found"
            mime_type = mimetypes.guess_type(filename)[0]            
            output_headers = self.__create_response_headers(status_line, "text/html", len(content))

            connection_socket.send(output_headers.encode())
            connection_socket.send(content.encode())
            connection_socket.send("\r\n".encode())
            connection_socket.close()
            file.close()
            self.logs.add_line(request_line, status_line, current_date, client_addr)

            
        except Exception as e:
            self.logs.add_error(e, current_date)
            connection_socket.close()

        self.counter_lock.acquire()        
        self.active_connections_counter -= 1
        print(f"Active Connections: {self.active_connections_counter:03}", end="\r")
        self.counter_lock.release()

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