import threading


mutex1 = threading.Lock()
mutex2 = threading.Lock()

def counter():
    for i in range(10):
        mutex1.acquire()
        print(i)
        mutex2.release()

def counter2():
    for i in range(10):
        mutex2.acquire()
        print(i)
        mutex1.release()
        
t1 = threading.Thread(target=counter)
t2 = threading.Thread(target=counter2)
mutex2.acquire()
t1.start()
t2.start()
