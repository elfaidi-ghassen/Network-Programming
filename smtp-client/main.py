import smtp_client

smtp_client.config(
  mailserver=("smtp.gmail.com", 465),
  user="elfaidighassen@gmail.com",
  password="odqr zkyx cfcj gxga"
)

smtp_client.send_mail(
  from_addr="elfaidighassen@gmail.com",
  to_addr="gha.faidi@gmail.com",
  subject="hello",
  text="a été detecté",
  # attachments=[
  #   {
  #     "filename": "cool.jpg",
  #     "path": "./ducks.jpg"
  #   },
  # ]
)