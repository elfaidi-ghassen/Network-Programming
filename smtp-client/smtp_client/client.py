import base64, ssl, mimetypes
from socket import socket, AF_INET, SOCK_STREAM

TRANSITIONS = {
  # current       new state      action to take
  "WAITING_FOR_GREETING": {
    "220": ("WAITING_FOR_HELO_RESPONSE", "SEND_HELO")
  },
  "WAITING_FOR_HELO_RESPONSE": {
    "250": ("WAITING_FOR_USERNAME_QUESTION", "SEND_AUTH_LOGIN")
  },
  "WAITING_FOR_USERNAME_QUESTION": {
    "334": ("WAITING_FOR_PASSWORD_QUESTION", "SEND_USER")
  },
  "WAITING_FOR_PASSWORD_QUESTION": {
    "334": ("WAITING_FOR_AUTH_ACCEPTED", "SEND_PASSWORD")
  },
  "WAITING_FOR_AUTH_ACCEPTED": {
    "235": ("WAITING_FOR_MAIL_FROM_ACCEPTED", "SEND_MAIL_FROM")
  },
  "WAITING_FOR_MAIL_FROM_ACCEPTED": {
    "250": ("WAITING_FOR_RCPT_TO_ACCEPTED", "SEND_RCPT_TO")
  },
  "WAITING_FOR_RCPT_TO_ACCEPTED": {
    "250": ("WAITING_FOR_GO_AHEAD", "SEND_DATA_COMMAND")
  },
  "WAITING_FOR_GO_AHEAD": {
    "354": ("SENDING_ATTACHMENTS", "SEND_EMAIL_TEXT"),
  },
  "SENDING_ATTACHMENTS": {
    "NO_ATTACHMENT": ("WAITING_FOR_EMAIL_RESPONSE", "SEND_DOT"),
    "NO_MORE_ATTACHMENTS": ("WAITING_FOR_EMAIL_RESPONSE", "SEND_DOT"),
    "MORE_ATTACHMENTS": ("SENDING_ATTACHMENTS", "SEND_NEXT_ATTACHMENT")
  },
  "WAITING_FOR_EMAIL_RESPONSE": {
    "250": ("DONE", "SEND_QUIT")
  }
}


class Client:
  def __init__(self):
    self.mailserver = None
    self.user = None
    self.password = None
  def base64(self, string):
    return base64.b64encode(string.encode("utf-8"))
  def set_mailserver(self, mailserver):
    if mailserver != ("smtp.gmail.com", 465):
      raise ValueError("Invalid mail server or port, only gmail is supported")
    self.mailserver = mailserver
  def set_user(self, user):
    self.user = user
  def set_password(self, password):
    self.password = password
  def send_mail(self, from_addr, to_addr, subject, text, attachments=None):
    if attachments == []:
      attachments = None
    if attachments:
      attachments = list(attachments) # shallow copy
  
    client_socket = socket(AF_INET, SOCK_STREAM)
    context = ssl.create_default_context()
    client_socket = context.wrap_socket(client_socket, server_hostname=self.mailserver[0])
    client_socket.connect(self.mailserver)
    current_state = "WAITING_FOR_GREETING"
    while current_state not in {"DONE", "ERROR"}:
      print(current_state)
      if current_state == "SENDING_ATTACHMENTS":
        if attachments == None:
          response = "NO_ATTACHMENT"
        else:
          response = "MORE_ATTACHMENTS" if attachments else "NO_MORE_ATTACHMENTS"
      else:
        response = client_socket.recv(1024).decode()
      found = False
      for expected_response in TRANSITIONS[current_state]:
        if response.startswith(expected_response):
          current_state, action = TRANSITIONS[current_state][expected_response]
          if action == "SEND_AUTH_LOGIN":
            client_socket.send("AUTH LOGIN\r\n".encode())
          elif action == "SEND_HELO":
            client_socket.send(f"HELO {self.mailserver[0]}\r\n".encode())
          elif action == "SEND_USER":
            client_socket.send(self.base64(self.user) + b"\r\n")
          elif action == "SEND_PASSWORD":
            client_socket.send(self.base64(self.password) + b"\r\n")
          elif action == "SEND_MAIL_FROM":
            client_socket.send(f"MAIL FROM: <{from_addr}>\r\n".encode())
          elif action == "SEND_RCPT_TO":
            client_socket.send(f"RCPT TO: <{to_addr}>\r\n".encode())
          elif action == "SEND_DATA_COMMAND":
            client_socket.send("DATA\r\n".encode())
          elif action == "SEND_EMAIL_TEXT":
            if not attachments:
              client_socket.send(self.get_singlepart_headers(from_addr, to_addr, subject, text))
            else:
              client_socket.send(self.get_multipart_headers(from_addr, to_addr, subject, text))
          elif action == "SEND_NEXT_ATTACHMENT":
            attachment = attachments.pop(0)
            client_socket.send(self.get_attachment_boundary(attachment))

            if not attachments: # no more attachments
              client_socket.send("--BOUNDARY--\r\n".encode())
          elif action == "SEND_DOT":
            client_socket.send(".\r\n".encode())
          elif action == "SEND_QUIT":
            client_socket.send("QUIT\r\n".encode())
          found = True
      if not found:
        current_state = "ERROR"
    client_socket.close()
    if current_state == "ERROR":
      raise Exception(f"Unexpected response: {response}")
  
  def get_singlepart_headers(self, from_addr, to_addr, subject, text):
    return "\r\n".join([
      f"From: {from_addr}",
      f"To: {to_addr}",
      f"Subject: {subject}",
      "Content-Transfer-Encoding: base64",
      "",
      self.base64(text).decode("ascii"),
      "\r\n", # empty line is required
    ]).encode("ascii")
  def get_multipart_headers(self, from_addr, to_addr, subject, text):
    return "\r\n".join([
      f"From: {from_addr}",
      f"To: {to_addr}",
      f"Subject: {subject}",
      "MIME-Version: 1.0",
      "Content-Type: multipart/mixed; boundary=BOUNDARY",
      "",
      "--BOUNDARY",
      'Content-Type: text/plain; charset="UTF-8"',
      "Content-Transfer-Encoding: base64",
      "",
      self.base64(text).decode("ascii") + "\r\n",
    ]).encode("ascii")
  def get_attachment_boundary(self, attachment):
    filename = attachment["filename"]
    path = attachment["path"]
    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type:
      raise Exception("Invalid File Type")

    with open(path, "rb") as file:
      data = file.read()

    return "\r\n".join([
      "--BOUNDARY",
      f'Content-Type: {mime_type}',
      f'Content-Disposition: attachment; filename="{filename}"',
      f"Content-Transfer-Encoding: base64",
      "",
      base64.b64encode(data).decode("ascii"),
      "",
    ]).encode("ascii")