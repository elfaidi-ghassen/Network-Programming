# Project 1: A Minimal Multithreaded Web Server

This project implements a multithreaded HTTP server in Python using the socket API. It features a custom thread pool to efficiently handle client-server communication and supports basic HTTP methods like GET and HEAD (with no support for POST). This project helped me see how HTTP works at a fundamental level — and it was a really fun learning experience!

One little expierement I did was to configure my home router to forward HTTP requests to my laptop (the server) using a port mapping, to bypass NAT protocol, thus allowing anyone in the internet to access the server.

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


