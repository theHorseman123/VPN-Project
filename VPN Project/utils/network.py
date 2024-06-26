import socket as sock
from cryptography import rsa_encrypt_message, rsa_decrypt_message

def connect_to_destination(destination_address: tuple):
    try:
        destination_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        destination_socket.connect(destination_address)
    except sock.error as error:
        print(f"socket error: {str(error)}")
        destination_socket.close()
        return

def send_message(destination_socket, message, destination_public_key = None):
    try:
        message = message.encode("utf-8")
        if destination_public_key:
            message = rsa_encrypt_message(destination_public_key)
            if not message:
                return
        
        destination_socket.sendall(message)
        return "pass"
    except sock.error as error:
        print(f"socket error: {str(error)}")
        destination_socket.close()
        return

def receive_message(source_socket, size, client_private_key = None):
    try:
        message = source_socket.recv(size)
        if message == "":
            print("sender has disconnected")
            return 
        
        if client_private_key:
            message = rsa_decrypt_message
        return message
    except sock.error as error:
        print(f"socket error: {str(error)}")
        source_socket.close()
        return 
        