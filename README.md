# Project 1: A Minimal Multithreaded Web Server

This project implements a multithreaded HTTP server in Python using the socket API. It features a custom thread pool to efficiently handle client-server communication and supports basic HTTP methods like GET and HEAD (but it doesn't support POST). This project helped me see how HTTP works at a fundamental level — and it was a really fun learning experience!

#### Notes
- **Serves static files**: Serves static files (e.g., HTML, CSS, JS, images) and generates directory listings dynamically (inspired by Apache server behavior).
- **Multithreading with a Custom Thread Pool**: 
  - Implements a thread pool using semaphores based on the producer-consumer pattern.
  - Manages concurrent client requests.
- **Supported HTTP Methods**: Supports `GET` and `HEAD` requests with proper handling of unsupported methods.
- **Logging**:
  - Logs client requests, server responses, and errors.
- **Active Connection Monitoring**:
  - Uses a simple thread-safe counter to track and display the number of active connections in real time.
- You can easily run the python script to run the server, you can optionally change the port number.
- to try it, you can use your browser for testing, by entering some thing like "localhost/index.html" as url
- I've wrote a simple client script to use for testing, `client.py`, which is like a simpler version of the `curl` command
- to try it, type in the command line `python client.py GET localhost 80 /index.html`

# Project 2: UDP PING

# Project 3: SMTP Client
A fully functional SMTP client for sending emails with attachments via Gmail's SMTP server.
*Features:*
- State Machine Architecture: Uses a finite state machine to orchestrate the SMTP protocol flow
- File Attachments: Supports multiple file attachments
- Base64 Encoding: Properly encodes email content and attachments per SMTP specifications


How to use it: (as you can see, the API is inspired by nodemailer)
```python
smtp_client.send_mail(
  from_addr="example@gmail.com",
  to_addr="someone@gmail.com",
  subject="hello",
  text="this is an example",
  attachments=[
    {
      "filename": "cool.jpg",
      "path": "./ducks.jpg"
    },
  ]
)
``
