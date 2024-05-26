import socket as sock
from select import select 
import argparse
import rsa
import scapy.all
from ..utils.network import *
from ..utils.cryptography import *
from select import select
from _thread import start_new_thread

SOCKS_VER = 5

SECRET_CODE = "secret-horsem4n-NMEX123"


def send(socket, data):
    try:
        socket.send(str(len(data)).zfill(8).encode() + data)
    except sock.error as error:
        print(f"ERROR: {str(error)}")

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
        print("no message size supllied")
        return

    message = b''
    while len(message) < message_size:
        try:
            msg_fragment = socket.recv(message_size - len(message))
        except sock.error as error:
            print(f"socket error: {str(error)}")
            return 
        
        if not msg_fragment:
            print("server has discconected")
            return 
        message = message + msg_fragment
    print(message)
    return message

class Proxy:

    def __init__(self, host:str="localhost", port:int=8080, server_address=("localhost", 1234) , secret_code:str=None) -> None:
        
        self.__host = host
        self.__port = port
        self.__proxy_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.__proxy_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.__secret_code = secret_code # The code to connect to the proxy

        self.__public_key, self.__private_key = generate_keys(1024, "proxy")

        self.__server_address = server_address
        self.__server_socket = None

        self.__clients = {}


    def __connect_to_server(self):
        try:
            self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.__server_socket.connect((self.__server_address, self.__server_port))
        except sock.error as error:
            print(f" ERROR: {str(error)}")
        
        data = receive(self.__server_socket)
        
        if not data:
            print("*Server disconnected")
            return 
        
        self.__server_public_key = rsa.PublicKey.load_pkcs1(data)
        send(self.__server_socket, self.__public_key.save_pkcs1("PEM"))

        data = "new_proxy//"
        if self.__secret_code: # sends the server if the proxy is locked or not
            data += data+"1"
        else:
            data += data+"0"
        encrypted_data = rsa_encrypt_message(data, self.__server_public_key)
        send(self.__server_socket, encrypted_data)
        encrypted_data = receive(self.__server_socket)
        
        if not data:
            print(" *Server disconnected")
            return
        
        data = rsa_decrypt_message(encrypted_data, self.__private_key)

        if data == "pass":
            return data
        
        else:
            print(data)
            return

    def __send_waiting_messages(self, messages_to_send: tuple, writeables):
        for message_to_send in messages_to_send:
            data, socket = message_to_send
            if socket in writeables:
                encrypted_data = rsa_encrypt_message(data, self.__clients[socket])
                send(socket, encrypted_data)

    def mainloop(self):
        status = self.__connect_to_server()
        if status != "pass":
            print(" *Closing connection with server")
            self.__server_socket.close()
            return
        self.__proxy_socket.bind((self.__host, self.__port))
        self.__proxy_socket.listen(5)

        messages_to_send = []

        print("* Starting proxy server")

        while 1:
            read_sockets, write_sockets, _ = select(self.__clients.keys+[self.__proxy_socket], self.__clients.keys, [])
            for read_socket in read_sockets:
                try:
                    if read_socket is self.__proxy_socket:
                        socket, _ = read_socket.accept()
                        start_new_thread(self.__connection_handler, (socket))
                    
                    else:
                        pass


                except sock.error as error:
                    print(f"ERROR: {error}")
                    print(" *Closing connection with:",(read_socket.getsockname()))
                    del self.__clients[read_socket]
                    read_socket.close()
            
            self.__send_waiting_messages(messages_to_send, write_sockets)

    def __client_handler(self, socket):
        pass

    def __requests_exchange_loop(self, client_socket, remote_socket):
        client_public_key = self.__clients[client_socket]
        while 1:
            read_socket, write_socket, _ = select([client_socket, remote_socket, []])

            if client_socket in read_socket:
                encrypted_data = receive(client_socket)
                if not encrypted_data:
                    return
                data = rsa_decrypt_message(encrypted_data, self.__private_key)
                send(remote_socket, data.encode("utf-8"))
            
            if remote_socket in read_socket:
                data = receive(remote_socket)
                if not data:
                    return
                encrypted_data = rsa_encrypt_message(data, client_public_key)
                send(client_socket, encrypted_data.encode("utf-8"))
                
    def __connection_handler(self, socket):
        try:
            if self.__secret_code:
                data = b"secret_code_required"
                send(socket, data) 
                # the client gets the proxy public key from the server
                encrypted_data = receive(socket)
                data = rsa_decrypt_message(encrypted_data, self.__private_key)
                if data != self.__secret_code:
                    data = b"wrong_code"
                    send(socket, data)
                    print(" *Closing connection with:",socket.getsockname())
                    socket.close()
                    return
                data = b"pass"
                send(socket, data)
            
            data = receive(socket)

            if not data:
                print(" *Closing connection with:", (socket.getsockname()))
                return
            
            client_public_key = rsa.PublicKey.load_pkcs1(data)

            self.__clients.update({socket:client_public_key})
                


        except sock.error as error:
            print(f"ERROR: {error}")
            print(" *Closing connection with:", (socket.getsockname()))


def main():
    # Create proxy object
    proxy = Proxy(host="10.100.102.93")

    # Start proxy
    proxy.mainloop()
    
if __name__ == '__main__':
    main()