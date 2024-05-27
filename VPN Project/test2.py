import socket
import ssl

# Proxy server configuration
HOST = 'localhost'
PORT = 12346

# Destination server configuration
DEST_HOST = 'destination.example.com'
DEST_PORT = 12345

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Proxy server listening on {}:{}".format(HOST, PORT))

# Wrap the socket with SSL
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="proxy.crt", keyfile="proxy.key")

with context.wrap_socket(server_socket, server_side=True) as ssl_socket:
    print("Proxy server: Secure connection established with client")

    conn, addr = ssl_socket.accept()

    with conn:
        print('Proxy server: Connection from', addr)

        # Receive data from client
        data = conn.recv(1024)
        print('Proxy server received from client:', data.decode())

        # Connect to the destination server
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_socket.connect((DEST_HOST, DEST_PORT))

        # Wrap the socket with SSL
        dest_ssl_socket = context.wrap_socket(dest_socket, server_hostname=DEST_HOST)
        print("Proxy server: Secure connection established with destination server")

        # Send data to destination server
        dest_ssl_socket.sendall(data)

        # Receive response from destination server
        response = dest_ssl_socket.recv(1024)
        print('Proxy server received from destination server:', response.decode())

        # Send response back to client
        conn.sendall(response)

        # Close the sockets
        dest_ssl_socket.close()