import socket
import sys
import time
import custom_http_requests
from datetime import datetime
import cache 

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
		return self.get_headers_data() + b"\r\n\r\n" + (self.get_body_data() or b"")
	
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
		return self.get_headers_data() + b"\r\n\r\n" + (self.get_body_data() or b"")
	
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
	requested = proxy_request.get_requested_resource()
	return requested.startswith("https://") or requested.startswith("/https://")



def still_valid_response(response, request, to_server_socket):
	last_modified = response.get_last_modified()
	if not last_modified:
		return
	if_modified_since = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")	
	headers = [*request.get_headers(), f"If-Modified-Since: {if_modified_since}"]
	request = Request(headers, "\r\n".join(headers).encode(), request.get_requested_resource(), request.get_method(), request.get_host(), request.get_body_data())
	to_server_socket.send(request.to_bytes())
	response = parse_response_stream(to_server_socket)
	return response.get_status_code() == 304

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
	_, status_code, *_ = headers[0].split() # HTTP/1.1 200 OK
	last_modified = get_header_value(headers, "Last-Modified")
	if last_modified:
		last_modified = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT") # RFC 1123 date format

	return Response(headers, headers_data, body_data, int(status_code), last_modified)

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
	memory_cache = cache.LRUCache(100)
	welcome_socket = create_tcp_socket((host, port))
	print("starting proxy server...")
	while True:
		connection_socket, _ = welcome_socket.accept()
		try:
			proxy_request = parse_request_stream(connection_socket)
		except Exception as e:
			connection_socket.send(custom_http_requests.BAD)
			continue
		
		if proxy_request.get_requested_resource() == "/favico.ico":
			continue

		if is_https(proxy_request):
			connection_socket.send(custom_http_requests.BAD_HTTPS)
			continue
		
		if proxy_request.get_method() not in {"GET", "POST"}:
			connection_socket.send(custom_http_requests.BAD_METHOD)
			continue
		
		request = create_request(proxy_request)
		to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		to_server_socket.connect((request.get_host(), 80))
		resource_path = proxy_request.get_requested_resource()
		if memory_cache.contains(resource_path):
			response = memory_cache.get(resource_path)
			if still_valid_response(response, request, to_server_socket):
				connection_socket.send(response.to_bytes())
				connection_socket.close()
				continue

		to_server_socket.send(request.to_bytes())
		server_response = parse_response_stream(to_server_socket)
		memory_cache.put(resource_path, server_response)
		connection_socket.send(server_response.to_bytes())
		connection_socket.close()
run_proxy("localhost", 8888)

# curl.exe -H "Connection: close" -H "User-Agent: MyProxy/1.0" -v http://localhost:8888/http://example.com/
