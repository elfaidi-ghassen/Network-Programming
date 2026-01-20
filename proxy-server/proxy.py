import socket
import ssl

import sys

TRANSITIONS = {
	# state        new state     action
	"INIT": {
		"DEFAULT": ("READING_REQUEST_HEADERS", None)
	},
	"READING_REQUEST_HEADERS": {
		"DONE": ("READING_REQUEST_BODY", "READ_REQUEST_BODY"),
		"ERROR": ("ERROR", None),
		"DEFAULT": ("READING_REQUEST_HEADERS", "READ_REQUEST_HEADER")
	}, 
	"READING_REQUEST_BODY": {
		"DEFAULT": ("READING_RESPONSE_HEADERS", "SEND_REQUEST")
		# "DEFAULT": ("DONE", "SEND_REQUEST")
	},
	"READING_RESPONSE_HEADERS": {
		"DONE": ("READING_RESPONSE_BODY", "READ_RESPONSE_BODY"),
		"ERROR": ("ERROR", None),
		"DEFAULT": ("READING_RESPONSE_HEADERS", "READ_RESPONSE_HEADERS")
	},
	"READING_RESPONSE_BODY": {
		"DEFAULT": ("INIT", "SEND_RESPONSE_BACK")
	}
}


HEADERS_TRANSITIONS = {
	# state        new state     action
	"READING_HEADERS": {
		"\r": ("SAW_CR", None),
		"DEFAULT": ("READING_HEADERS", "ADD_CHAR")
	},

	"SAW_CR": {
		"\n": ("SAW_CRLF", None),
		# otherwise error
	},
	"SAW_CRLF": {
		"\r": ("SAW_CRLFCR", "ADD_HEADER_LINE"),
		"DEFAULT": ("READING_HEADERS", "ADD_HEADER_NEW_CHAR")
	},

	"SAW_CRLFCR": {
		"\n": ("DONE", None)
		# otherwise error
	}
}

# after that read the body based on content length
class HeadersReaderFSM:
	def __init__(self):
		self.headers = []
		self.current_state = "READING_HEADERS"
		self.current_header = ""
	def next(self, char):
		if self.current_state in {"DONE", "ERROR"}:
			return
		if char in HEADERS_TRANSITIONS[self.current_state]:
			self.current_state, action = HEADERS_TRANSITIONS[self.current_state][char]
		elif "DEFAULT" in HEADERS_TRANSITIONS[self.current_state]:
			self.current_state, action = HEADERS_TRANSITIONS[self.current_state]["DEFAULT"]
		else:
			self.current_state = "ERROR"
		
		if action == "ADD_CHAR":
			self.current_header += char
		elif action == "ADD_HEADER_LINE":
			self.headers.append(self.current_header)
			self.current_header = ""
		elif action == "ADD_HEADER_NEW_CHAR":
			self.headers.append(self.current_header)
			self.current_header = char
	
	def get_headers(self):
		return self.headers.copy()
	def get_current_state(self):
		return self.current_state
	def reset(self):
		self.current_state = "READING_HEADERS"
		self.headers.clear()

class ProxyServer:
	def __init__(self, host, port):
		self.hostname = host
		self.port = port
	def start(self):
		try:

			self.welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.welcome_socket.bind((self.hostname, self.port))
			self.welcome_socket.listen(5)
			print("server has started")
			while True:
				connection_socket, client_address = self.welcome_socket.accept()
				request_headers = None
				request_body = None
				server_response_headers = None
				server_response_body = None
				current_input = None
				self.current_state = "INIT"
				while True:
					print(self.current_state)
					print(current_input)
					if self.current_state in {"ERROR", "DONE"}:
						print(request_headers)
						print(request_body)
						break
					if current_input in TRANSITIONS[self.current_state]:
						self.current_state, action = TRANSITIONS[self.current_state][current_input]
					elif "DEFAULT" in TRANSITIONS[self.current_state]:
						self.current_state, action = TRANSITIONS[self.current_state]["DEFAULT"]
					else:
						self.current_state, action = "ERROR", None

					if action == "READ_REQUEST_HEADER":
						reader = HeadersReaderFSM()
						msg = connection_socket.recv(1024).decode()
						for char in msg:
							reader.next(char)
							if reader.get_current_state() == "ERROR":
								current_input = reader.get_current_state()
								break
							if reader.get_current_state() == "DONE":
								current_input = reader.get_current_state()
								request_headers = reader.get_headers()
					if action == "READ_REQUEST_BODY":
						length = self.get_content_length(request_headers)
						read_bytes = b""
						while len(read_bytes) < length:
							read_bytes += connection_socket.recv(1024)
						request_body = read_bytes if length else None 
						current_input = None

					if action == "READ_RESPONSE_HEADERS":
						to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						print(self.get_server_address(request_headers))
						address = self.get_server_address(request_headers)
						to_server_socket.connect(address)

						new_request_headers = request_headers.copy()
						full_path = new_request_headers[0].split()[1]  # '/www.example.com/index.html'
						full_path = full_path.lstrip('/')
						host, _, path = full_path.partition('/')  # host='www.example.com', path='index.html'
						if path:
								path = '/' + path
						else:
								path = '/'

						method = new_request_headers[0].split()[0]
						version = new_request_headers[0].split()[2]

						new_request_headers[0] = f"{method} {path} {version}"
						new_request_headers[1] = f"Host: {host}"

						to_server_socket.send(self.to_request_bytes(new_request_headers, request_body))
						reader = HeadersReaderFSM()
						msg = to_server_socket.recv(1024).decode()
						for char in msg:
							reader.next(char)
							if reader.get_current_state() == "ERROR":
								current_input = reader.get_current_state()
								break
							if reader.get_current_state() == "DONE":
								current_input = reader.get_current_state()
								server_response_headers = reader.get_headers()
								break

					if action == "READ_RESPONSE_BODY":
						length = self.get_content_length(server_response_headers)
						print("length", length)
						read_bytes = b""
						while len(read_bytes) < length:
							data = to_server_socket.recv(1024)
							if data == b"":
								break
							read_bytes += data
						server_response_body = read_bytes if length else None 
					
					if action == "SEND_RESPONSE_BACK":
						response = self.to_response_bytes(server_response_headers, server_response_body)
						connection_socket.send(response)
						connection_socket.close()
						to_server_socket.close()
		except KeyboardInterrupt:
			print("Shutting down server...")
		finally:
			self.welcome_socket.close()

	def to_request_bytes(self, request_headers, request_body):
		return ("\r\n".join(request_headers) + "\r\n\r\n").encode() + (request_body or b"")
	def to_response_bytes(self, server_response_headers, server_response_body):
		return ("\r\n".join(server_response_headers) + "\r\n\r\n").encode() + (server_response_body or b"")
	
	def get_server_address(self, request_headers):
		full_path = request_headers[0].split()[1].lstrip('/')
		host, _, _ = full_path.partition('/')
		return (host, 80)

	def get_content_length(self, headers):
		length = 0
		for header in headers:
			if header.startswith("Content-Length:"):
				length = int(header.split(":")[1])
		return length
