import threading

class ThreadPool:
    """
    Using the producer-consumer pattern
    """
    def __init__(self, callback, MAX_WORKERS, QUEUE_SIZE):
        self.MAX_WORKERS = MAX_WORKERS
        self.QUEUE_SIZE = QUEUE_SIZE
        self.callback = callback
        
        self.full = threading.Semaphore(0)
        self.empty = threading.Semaphore(QUEUE_SIZE)
        self.mutex = threading.Semaphore(1)
        self.tasks_queue = []
        self.running = True
        self.workers = [threading.Thread(target=self.__worker) for _ in range(MAX_WORKERS)]
        for thread in self.workers:
            thread.start()

    def __worker(self):
        while self.running:
            self.full.acquire()
            if self.running == False:
                break
            try: # callback(task) could throw an error
                with self.mutex:
                    task = self.tasks_queue.pop(0)
                    self.callback(task)
            finally:
                self.empty.release()
    def close(self):
        self.running = False
        for _ in range(self.MAX_WORKERS):
            self.full.release()
    def add_task(self, task):
        self.empty.acquire()
        with self.mutex:
            self.tasks_queue.append(task)
        self.full.release()

