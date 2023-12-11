# VPN-Project

## First Milestone: simple proxy connection

For the first milestone I crated three diffrent file: proxy.py, server.py, client.py. that I will explain one by one.

### Let's start with the server: 

The server file has a class that binds a socket

<sup>
# bind socket to address 
  self.sock.bind((self.host, self.port))
  self.sock.listen(5)
  print("Starting server on:", (self.host, self.port))
</sup>

