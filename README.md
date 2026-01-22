# Networking Projects

These projects were built from scratch using only Python's standard library (socket, threading, base64, etc.), without relying on high-level web frameworks or HTTP libraries. 
These are the programming assignments in Computer Networks: A Top-Down Approach (one of the coolest CS books I've encountered) The book's hands-on approach to networking helped me understand how protocols actually work at a fundamental level.

NB: These projects are made for learning purpous, to understand socket programming and how application layer protocols work, I didn't focus on areas like security and edge cases of each protocol

---

## Project 1: Multithreaded HTTP Web Server

A minimal multithreaded http server used to serve static content.

### Features
- **Multithreaded Architecture**: Custom thread pool using semaphores (producer-consumer pattern) for efficient concurrent connection handling
- **Static File Serving**: Serves HTML, CSS, JS, images, and other static assets with MIME type detection
- **Directory Listings**: Dynamically generates Apache-style directory listings
- **HTTP Methods**: Supports `GET` and `HEAD` requests
- **Connection Monitoring**: Thread-safe counter tracking active connections in real-time
- **Logging**: Logs client requests, server responses, and errors

### Usage
```bash
python server.py                    # Default: localhost:8080
python server.py --port 8989        # Custom port
```

Test with your browser:
```
http://localhost:8080/index.html
```

Or use the client script:
```bash
python client.py GET localhost 80 /index.html
python client.py HEAD localhost 80 /
```

---

## Project 2: HTTP Forward Proxy

An HTTP proxy server with request forwarding, caching, and conditional GET support.

### Features
- **Request Forwarding**: Parses client requests, transforms them, and forwards to origin servers
- **LRU Cache**: Custom doubly-linked list + hashmap implementation
- **Conditional GET**: Validates cached responses using `If-Modified-Since` headers (HTTP 304 Not Modified)

### Usage
```bash
python proxy.py      # Starts on localhost:8888
```
You can set the proxy in the OS network settings to localhost:8888. As a result, all requests will be forwarded to the proxy.
the requests will be in this format
```http
GET http://www.example.com/image.png HTTP/1.1
Host: www.example.com
```
later the proxy will transform the request into this:
```http
GET /image.png HTTP/1.1
Host: www.example.com
```

Hence, if you don't want to change the proxy settings, you can test it using curl:
```bash
curl.exe -H "Connection: close" -H "User-Agent: Something/1.0" -v http://localhost:8888/http://example.com/
```

---

## Project 3: UDP Ping

A Simple UDP-based ping utility demonstrating connectionless socket programming.

### Features
- **Echo Protocol**: Sends ICMP-like echo requests over UDP
- **Round Trip Time**: Measures and displays latency
- **Packet Loss Detection**: Handles timeouts and unreachable hosts

### Usage
```bash
python ping.py <host>
python ping.py localhost 
```

---

## Project 4: SMTP Client

A fully functional SMTP client for sending emails with attachments via Gmail's SMTP server.

### Features
- **State Machine Architecture**: Finite state machine orchestrates SMTP protocol flow
- **Email Attachments**: Supports multiple file attachments with proper encoding
- **Base64 Encoding**: Properly encodes content and attachments per SMTP specifications
- **Gmail Integration**: Works with Gmail's SMTP server (requires app-specific password)

### Usage
```python
from smtp_client import SMTPClient

client = SMTPClient(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password"
)

client.send_mail(
    from_addr="your-email@gmail.com",
    to_addr="recipient@example.com",
    subject="Hello from Python!",
    text="This is the email body",
    attachments=[
        {
            "filename": "document.pdf",
            "path": "./documents/file.pdf"
        },
        {
            "filename": "image.jpg",
            "path": "./images/photo.jpg"
        }
    ]
)
```


### Lessons Learned
1. **TCP is streaming**: `recv()` doesn't guarantee full messages
  it's similar to the concept of stream (and lazy evaluation) in programming, you keep reading and you don't really know what's gonna come up next! so the idea is to keep reading until you reach a protocol-defined delimiter like "\r\n\r\n", or read some well known number of bytes, for instance after reading Content-Length, you can use that value to read the body of the HTTP request (or response)
2. **Parsing HTTP is hard**, Well I guess parsing anything is hard. but it's really full of edge cases and some missing or extra "/".
3. TCP is amazing, one of the coolest abstractions I've ever seen, it's just, you open a socket, and you can rest assured it will be delivered. it's amazing how it's built over something unreliable like the IP protocol
4. **I Fell in Love with CS**: The moment I saw the HTTP server working, I realized I really love this field. Simple projects like these makes you appreciate how everything fits together.