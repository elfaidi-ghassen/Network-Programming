import threading
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

