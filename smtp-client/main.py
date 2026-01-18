import smtp_client

smtp_client.config(
  mailserver=("smtp.gmail.com", 465),
  user="elfaidighassen@gmail.com",
  password="PASSWORD HERE"
)

smtp_client.send_mail(
  from_addr="elfaidighassen@gmail.com",
  to_addr="gha.faidi@gmail.com",
  subject="hello",
  text="this is an example",
  attachments=[
    {
      "filename": "cool.jpg",
      "path": "./ducks.jpg"
    },
  ]
)