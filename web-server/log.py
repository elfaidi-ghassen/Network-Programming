import threading
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

