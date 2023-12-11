# VPN-Project

## First Milestone: simple proxy connection

For the first milestone I crated three diffrent file: proxy.py, server.py, client.py. that I will explain one by one.

### Let's start with the server: 

The server is used to demonstrate an external server the client want to send a request to.
Once the server gets a message he will echo it back we'll know if he got the message.

### Next the proxy: 

The proxy is the "bridge" between the server and the client. Once he gets a message he'll check if the message is from the server, if it is, he'll send it
to all the connected clients, and if not, he'll send the message forward to the server.

### And the client:

The client is a simple loop that gets an input from the user and sends it to the proxy and if he gets messsage he'll print them.

