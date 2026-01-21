BAD_HTTPS = b"HTTP/1.1 400 Bad Request\r\n" + \
      b"Connection: close\r\n" + \
      b"Content-Length: 19\r\n" + \
      b"\r\n" + \
      b"HTTPS not supported"

BAD_METHOD = b"HTTP/1.1 400 Bad Request\r\n" + \
      b"Connection: close\r\n" + \
      b"Content-Length: 31\r\n" + \
      b"\r\n" + \
      b"Only GET and POST are supported"

BAD = b"HTTP/1.1 400 Bad Request\r\n" + \
      b"Connection: close\r\n" + \
      b"Content-Length: 0\r\n" + \
      b"\r\n"