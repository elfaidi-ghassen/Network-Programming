import socket
import sys
import time
import http
from datetime import datetime

# forward proxy
# to test
# curl.exe http://localhost:8888/www.vulnweb.com/index
#
# GET www.vulnweb.com/index HTTP/1.1
# Host: http://localhost:8888
#
# the proxy sends:
# GET /index HTTP/1.1
# Host: www.vulnweb.com

class Request:
	def __init__(self, headers=None, headers_data=b"", requested_resource=None, method=None, host=None, body_data=b""):
		self._headers = headers if headers else []
		self._headers_data = headers_data
		self._requested_resource = requested_resource
		self._method = method
		self._host = host
		self._body_data = body_data

	def get_headers_data(self):
		return self._headers_data
	

	def get_headers(self):
		return self._headers.copy()
		
	def add_header(self, header):
		self._headers.append(header)
	
	def get_requested_resource(self):
		return self._requested_resource
		
	def get_method(self):
		return self._method
	
	def get_host(self):
		return self._host
	
	def get_body_data(self):
		return self._body_data

	def to_bytes(self):
		return self.get_headers_data() + b"\r\n\r\n" + self.get_body_data()
	
	def __str__(self):
		return self.to_bytes().decode()


class Response:
	def __init__(self, headers, headers_data, body_data, status_code, last_modified):
		self._headers = headers if headers else []
		self._headers_data = headers_data
		self._body_data = body_data
		self._status_code = status_code
		self._last_modified = last_modified

	def get_headers(self):
		return self._headers.copy()
		
	def get_headers_data(self):
		return self._headers_data
	
	def get_body_data(self):
		return self._body_data
		
	def get_status_code(self):
		return self._status_code
	
	def get_last_modified(self):
		return self._last_modified
	
	def to_bytes(self):
		return self.get_headers_data() + b"\r\n\r\n" + self.get_body_data()
	
	def __str__(self):
		return self.to_bytes().decode()

def create_tcp_socket(address, backlog=5):
	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp_socket.bind(address)
	tcp_socket.listen(5)
	return tcp_socket


def get_header_value(headers, header_name):
	content_length = list(filter(lambda header : header.startswith(f"{header_name}:"), headers))
	if content_length:
		return content_length[0].partition(":")[2].strip()
	else:
		return None

def is_https(proxy_request):
		return proxy_request.get_requested_resource().startswith("https://")

def parse_request_stream(socket):
	headers_data = b""
	while b"\r\n\r\n" not in headers_data:
		headers_data += socket.recv(1024)
	headers_data, body_data = headers_data.split(b"\r\n\r\n")
	headers = headers_data.decode().split("\r\n")
	content_length = get_header_value(headers, "Content-Length")
	if content_length:
		content_length = int(content_length)
	while content_length != None and len(body_data) < content_length:
		body_data += socket.recv(1024)
	host = get_header_value(headers, "Host")
	method, requested_resource, _ = headers[0].split()
	return Request(headers, headers_data, requested_resource, method, host, body_data)

def parse_response_stream(socket):
	headers_data = b""
	while b"\r\n\r\n" not in headers_data:
		headers_data += socket.recv(1024)
	headers_data, body_data = headers_data.split(b"\r\n\r\n")
	headers = headers_data.decode().split("\r\n")
	content_length = get_header_value(headers, "Content-Length")
	if content_length:
		content_length = int(content_length)
	while content_length != None and len(body_data) < content_length:
		body_data += socket.recv(1024)
	_, status_code, _ = headers[0].split() # HTTP/1.1 200 OK
	last_modified = get_header_value(headers, "Last-Modified")
	if last_modified:
		last_modified = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT") # RFC 1123 date format

	return Response(headers, headers_data, body_data, status_code, last_modified)

def create_request(proxy_request):
	# GET www.vulnweb.com/index HTTP/1.1 ---> GET /index HTTP/1.1
	# Host: http://localhost:8888 ---> www.vulnweb.com
	host, _, resource = proxy_request.get_requested_resource().lstrip("http://").lstrip("/").partition("/")
	if not resource:
		resource = "/"
	else:
		resource = "/" + resource
	headers = proxy_request.get_headers()
	headers[0] = f"{proxy_request.get_method()} {resource} HTTP/1.1"
	headers[1] = f"Host: {host}"
	return Request(headers, "\r\n".join(headers).encode(), resource, proxy_request.get_method(), host, proxy_request.get_body_data())

def run_proxy(host, port):
		memory_cache = {}
		welcome_socket = create_tcp_socket((host, port))
		while True:
			connection_socket, _ = welcome_socket.accept()
			try:
				proxy_request = parse_request_stream(connection_socket)
			except Exception as e:
				connection_socket.send(http.BAD)
				continue
			
			if proxy_request.get_requested_resource() == "/favico.ico":
				print("annoying favico")
				continue

			if is_https(proxy_request):
				connection_socket.send(http.BAD + "HTTPS not supported".encode())
				continue
			
			if proxy_request.get_method() not in {"GET", "POST"}:
				connection_socket.send(http.BAD + f"{proxy_request.get_method()} is not supported".encode())
				continue
			


			if proxy_request.get_requested_resource() in memory_cache:
				response = memory_cache[proxy_request.get_requested_resource()]
				connection_socket.send(response.to_bytes())
				connection_socket.close()
				print("FROM CACHE!")
				continue


			request = create_request(proxy_request)
			to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			print("=================")
			print(request.get_host())
			print(proxy_request)
			print(request)
			print("=================")


			to_server_socket.connect((request.get_host(), 80))

			to_server_socket.send(request.to_bytes())
			server_response = parse_response_stream(to_server_socket)
			memory_cache[proxy_request.get_requested_resource()] = server_response
			connection_socket.send(server_response.to_bytes())
			connection_socket.close()
run_proxy("localhost", 8888)

# curl.exe -H "Connection: close" -H "User-Agent: MyProxy/1.0" -v http://localhost:8888/http://example.com/




# class ProxyServer:
# 	def __init__(self, host, port):
# 		self.hostname = host
# 		self.port = port
# 	def start(self):
# 		try:
# 			self.welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 			self.welcome_socket.bind((self.hostname, self.port))
# 			self.welcome_socket.listen(5)
# 			print("server has started")
# 			while True:
# 				connection_socket, client_address = self.welcome_socket.accept()
# 				request_headers = None
# 				request_body = None
# 				server_response_headers = None
# 				server_response_body = None
# 				current_input = None
# 				self.current_state = "INIT"
# 				while True:
# 					if self.current_state in {"ERROR", "DONE"}:
# 						break
# 					if current_input in TRANSITIONS[self.current_state]:
# 						self.current_state, action = TRANSITIONS[self.current_state][current_input]
# 					elif "DEFAULT" in TRANSITIONS[self.current_state]:
# 						self.current_state, action = TRANSITIONS[self.current_state]["DEFAULT"]
# 					else:
# 						self.current_state, action = "ERROR", None

# 					if action == "READ_REQUEST_HEADER":
# 						reader = HeadersReaderFSM()
# 						msg = connection_socket.recv(1024)
# 						if not msg:
# 							connection_socket.close()
# 							break
# 						msg = msg.decode()
# 						for char in msg:
# 							reader.next(char)
# 							if reader.get_current_state() == "ERROR":
# 								current_input = reader.get_current_state()
# 								break
# 							if reader.get_current_state() == "DONE":
# 								current_input = reader.get_current_state()
# 								request_headers = reader.get_headers()

# 					if action == "READ_REQUEST_BODY":
# 						length = self.get_content_length(request_headers)
# 						read_bytes = b""
# 						while len(read_bytes) < length:
# 							read_bytes += connection_socket.recv(1024)
# 						request_body = read_bytes if length else None 
# 						current_input = None

# 					if action == "SEND_REQUEST":
# 						method = request_headers[0].split()[0]
# 						if method == "CONNECT":
# 							connection_socket.close()
# 							print("UNSUPPORTED")
# 							break

# 						# print(request_headers[0])
# 						# print(self.get_server_address(request_headers))
# 						to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 						address = self.get_server_address(request_headers)
# 						if address[0] == "favicon.ico":
# 							connection_socket.close()
# 							break
# 						to_server_socket.connect(address)
# 						new_request_headers = request_headers.copy()
# 						full_path = new_request_headers[0].split()[1]  # 'http://www.example.com/index.html'
# 						full_path = full_path.lstrip('http://')
# 						full_path = full_path.lstrip('/')
# 						host, _, path = full_path.partition('/')  # host='www.example.com', path='index.html'
# 						if path:
# 								path = '/' + path
# 						else:
# 								path = '/'
# 						method = new_request_headers[0].split()[0]
# 						version = new_request_headers[0].split()[2]

# 						new_request_headers[0] = f"{method} {path} {version}"
# 						new_request_headers[1] = f"Host: {host}"
# 						print(new_request_headers[0])
# 						to_server_socket.send(self.to_request_bytes(new_request_headers, request_body))


# 					if action == "READ_RESPONSE_HEADERS":
# 						# what.. if... we read more than what we need in the header?
# 						reader = HeadersReaderFSM()
# 						# msg = to_server_socket.recv(1).decode()
# 						# print(msg, end="")
# 						msg = to_server_socket.recv(1024)
# 						for i, char in enumerate(msg):
# 							reader.next(chr(char))
# 							if reader.get_current_state() == "ERROR":
# 								current_input = reader.get_current_state()
# 								break
# 							if reader.get_current_state() == "DONE":
# 								current_input = reader.get_current_state()
# 								server_response_headers = reader.get_headers()
# 								if i < len(msg) - 1:
# 									server_response_body = msg[i + 1:]
								
# 								break

# 					if action == "READ_RESPONSE_BODY":
# 						length = self.get_content_length(server_response_headers)
# 						# print("length", length)
						
# 						read_bytes = b""
# 						while len(read_bytes) < (length - len(server_response_body or b"")):
# 							data = to_server_socket.recv(1024)
# 							# if data == b"":
# 							# 	break
# 							read_bytes += data
# 						if server_response_body == None:
# 							server_response_body = b""
# 						server_response_body += read_bytes
# 						if not length:
# 							 server_response_body = None
					
# 					if action == "SEND_RESPONSE_BACK":
# 						response = self.to_response_bytes(server_response_headers, server_response_body)
# 						print("yo, it's here!")
# 						connection_socket.send(response)
# 						connection_socket.close()
# 						to_server_socket.close()



# 		except KeyboardInterrupt:
# 			print("Shutting down server...")
# 		finally:
# 			self.welcome_socket.close()

# 	def to_request_bytes(self, request_headers, request_body):
# 		return ("\r\n".join(request_headers) + "\r\n\r\n").encode() + (request_body or b"")
# 	def to_response_bytes(self, server_response_headers, server_response_body):
# 		return ("\r\n".join(server_response_headers) + "\r\n\r\n").encode() + (server_response_body or b"")
	
# 	def get_server_address(self, request_headers):

# 		full_path = request_headers[0].split()[1].lstrip('http://')
# 		host, _, _ = full_path.partition('/')
# 		return (host, 80)

# 	def get_content_length(self, headers):
# 		length = 0
# 		for header in headers:
# 			if header.startswith("Content-Length:"):
# 				length = int(header.split(":")[1])
# 		return length
