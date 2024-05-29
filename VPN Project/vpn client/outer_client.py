import socket as sock
from select import select
from _thread import start_new_thread


def send(socket, data):
    try:
        socket.send(str(len(data)).zfill(8).encode() + data)
    except sock.error as error:
        print(f"socket error: {str(error)}")

def receive(socket:sock):
    try:
        message_size = socket.recv(8)
    except sock.error as error:
        print(f"ERROR: {str(error)}")
        return 
    if message_size == b"":
        return
    try:
        message_size = int(message_size)
    except ValueError:
        return

    message = b''
    while len(message) < message_size:
        try:
            msg_fragment = socket.recv(message_size - len(message))
        except sock.error as error:
            print(f"ERROR: {str(error)}")
            return 
        
        if msg_fragment == b"":
            print(" INFO: socket has discconected at:", (socket.getsockname()))
            return 
        message = message + msg_fragment
    return message



def client_handler(socket):
    while 1:
        data = socket.recv(1024)
        
        if data == b"":
            return
        
        
        print(data)
        

server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
server_socket.bind(("localhost", 1234))
server_socket.listen(5)
print(" *Starting server on", (server_socket.getsockname()))

while 1:
    
    socket, addr = server_socket.accept()
    print(" *New connection from:", (socket.getsockname()))
    start_new_thread(client_handler, (socket, ))

