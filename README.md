# VPN-Project

### Server: 

The server binds to an address and wait for clients and proxies requests.
The server can save new proxies and send clients their address.

### Proxy: 

The proxy uses an implementation of the protocol Socks5 which is a secure protocol that supports proxying of packets.

### Client:

The client firstly asks the server for addresses of proxies and then connects to it and exchanges data according to the protocol.

