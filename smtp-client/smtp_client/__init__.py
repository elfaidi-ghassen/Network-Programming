from .client import Client

client = Client()
def config(mailserver, user, password):
  client.set_mailserver(mailserver)
  client.set_user(user)
  client.set_password(password)

def send_mail(from_addr, to_addr, subject, text, attachments=None):
  client.send_mail(from_addr, to_addr, subject, text, attachments)

__all__ = ['config', 'send_mail']