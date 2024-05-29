import socket as sock
from _thread import start_new_thread

def client_handler(socket):
    while 1:
        data = socket.recv(1024)
        
        if data == "":
            return
        
        print(data)

server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
server_socket.bind(("localhost", 1234))
server_socket.listen(5)
print(" *Starting server on", (server_socket.getsockname()))

while 1:
    
    socket, _ = server_socket.accept()
    print(" *New connection from:", (socket.getsockname()))
    start_new_thread(client_handler, (socket, ))

