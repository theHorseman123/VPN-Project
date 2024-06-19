import socket as sock
from select import select 
import argparse
import sys
import os
import rsa
from scapy.all import get_if_addr
from select import select
from _thread import start_new_thread

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.cryptography import *

PROXY_SECRET_KEY = aes_generate_key("secret-horseman-NMEX123")


def send(socket, data):
    try:
        socket.send(str(len(data)).zfill(8).encode() + data)
    except sock.error as error:
        print(f"ERROR: {str(error)}")

def receive(socket:sock):
    try:
        message_size = socket.recv(8)
    except sock.error as error:
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
            return 
        
        if msg_fragment == b"":
            print(" INFO: socket has discconected at:", (socket.getsockname()))
            return 
        message = message + msg_fragment
    return message

class Proxy:

    def __init__(self, host:str=None, port:int=None, server_address=None , secret_code:str=None, interface=None) -> None:
        if interface:
            try:
                if not host:
                    host = get_if_addr(interface)
                if not server_address:
                    server_address = (get_if_addr(interface), 1234)
            except Exception as error:
                pass
        if not host:
            host = "localhost"
        if not server_address:
            server_address=("localhost", 1234)
        if not port:
            port = 8080
        
        self.__host = host
        self.__port = port
        self.__proxy_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.__proxy_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.__secret_code = secret_code # The code to connect to the proxy

        self.__public_key, self.__private_key = generate_keys(1024)

        self.server_address = server_address
        self.__server_key = aes_generate_key()
        self.__server_socket = None

        self.__clients = {}
        self.__sessions = {}

    def __close_connection(self, socket, addr):
        print(" *Closing connection with:",(addr))
        del self.__clients[socket]
        socket.close()

    def __connect_to_server(self):
        try:
            self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.__server_socket.connect(self.server_address)
        except sock.error as error:
            print(f" ERROR: {str(error)}")
        
        data = receive(self.__server_socket)
        
        if not data:
            self.__server_socket.close()
            return 
        
        server_public_key = rsa.PublicKey.load_pkcs1(data)
        symmetric_key = aes_retreive_key(self.__server_key).decode()
        encrypted_key = rsa_encrypt_message(symmetric_key, server_public_key)
        send(self.__server_socket, encrypted_key)
        encrypted_data = receive(self.__server_socket)
        
        if not data:
            self.__server_socket.close()
            return 
        
        data = self.__server_key.decrypt(encrypted_data)
        if not data == b"pass":
            print(f" INFO: cant connect to server({data.decode()})")
            self.__server_socket.close()
            return 
        
        address = (f"{self.__host}:{int(self.__port)}|").encode()
        data_layer2 = b"new_proxy//"
        
        data_layer1 = address

        if self.__secret_code: # sends the server if the proxy is locked or not
            data_layer1 += b"1|"
        else:
            data_layer1 += b"0|"

        # Sending proxy commands requires another layer of encryption
        data_layer1 += (self.__public_key.save_pkcs1("PEM"))
        encrypted_data = self.__server_key.encrypt(data_layer2+PROXY_SECRET_KEY.encrypt(data_layer1))
        send(self.__server_socket, encrypted_data)
        encrypted_data = receive(self.__server_socket)
        
        if not data:
            print(" *Server disconnected")
            return
        
        data = self.__server_key.decrypt(encrypted_data).decode()
        if data == "pass":
            return data
        
        print(f" INFO: {data}")
        return

    def __send_waiting_messages(self, messages_to_send: tuple, writeables):
        for message_to_send in messages_to_send:
            data, socket = message_to_send
            if socket in writeables:
                encrypted_data = self.__clients[socket].encrypt(data)
                send(socket, encrypted_data)

    def mainloop(self):
        status = self.__connect_to_server()
        if status != "pass":
            print(" *Closing connection with server")
            self.__server_socket.close()
            return
        self.__proxy_socket.bind((self.__host, self.__port))
        self.__proxy_socket.listen(5)

        print("* Starting proxy server")

        while 1:
            try:
                socket, addr = self.__proxy_socket.accept()
                print(f" INFO: New connection from:", (addr))
                start_new_thread(self.__client_handler, (socket, addr))
            except sock.error as error:
                print(f"ERROR: {str(error)}")   

    def __client_handler(self, socket, addr):
        encrypted_data = receive(socket)
        session_id = rsa_decrypt_message(encrypted_data, self.__private_key)
        if session_id in self.__sessions.keys():
            client_key = self.__sessions[session_id]
            send(socket, client_key.encrypt(b"pass"))

        else:
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
            
            send(socket, b"send_key")

            encrypted_data = receive(socket)
            key = rsa_decrypt_message(encrypted_data, self.__private_key)

            try:
                client_key = Fernet(key)
                session_id = generate_random_base64(8)
                encrypted_data = client_key.encrypt(session_id.encode("utf-8"))
                send(socket, encrypted_data)
                self.__sessions.update({session_id:(client_key)})
            except Exception as error:
                print(f" ERROR: {str(error)}")
                print(" *Closing connection with:", (addr))
                raise error
            
        self.__clients.update({socket:client_key})
            
        print(" INFO: New client from:", (addr)) 

        encrypted_data = receive(socket)
        if not encrypted_data:
            self.__close_connection(socket, addr)
            return
        data = client_key.decrypt(encrypted_data)
        if data.split(b" ")[0] == b"CONNECT": # The proxy only accepts HTTPS requests
            self.__requests_exchange_loop(socket, data)
        else:
            # The proxy only allows secured http requests
            response = "HTTP/1.1 405 Not Allowed\r\n"
            response += "Content-Type: text/html\r\n"
            response += "\r\n"
            response += "<h1>The Horseman Tunnels service has blocked your connection.</h1>"
            socket.send(response.encode("utf-8"))
                
        socket.close()

    def __requests_exchange_loop(self, client_socket, request):
        
        client_key = self.__clients[client_socket]

        host, port = request.split(b" ")[1].split(b":")
        remote_address = (host.decode(), int(port))
        remote_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        try:
            remote_socket.connect(remote_address)
            print(" INFO: Established connection with:", (remote_address))
        except sock.error as error:
            print(f" ERROR: {error}")
            send(client_socket, client_key.encrypt(b"send"))
            return
        
        data = "HTTP/1.0 200 Connection established\r\n"
        data += "Proxy-agent: Horseman-tunnels\r\n"
        data += "\r\n"
        send(client_socket, client_key.encrypt(data.encode()))

        
        client_key = self.__clients[client_socket]
        try:
            while 1:
                read_socket, _, _ = select([client_socket, remote_socket], [], [])

                if client_socket in read_socket:
                    encrypted_data = receive(client_socket)

                    if not encrypted_data:
                        return
                    
                    data = client_key.decrypt(encrypted_data)
                    remote_socket.sendall(data)
                
                if remote_socket in read_socket:
                    data = remote_socket.recv(4096)

                    if data == b"":
                        send(client_socket, client_key.encrypt(b'close'))
                        return
                    
                    encrypted_data = client_key.encrypt(data)
                    send(client_socket, encrypted_data)
        except:
            send(client_socket, client_key.encrypt(b'close'))
            return
        
def main():

    parser = argparse.ArgumentParser(description='This is the code for the proxy server')
    parser.add_argument("--server",  type=str, help="insert: server_host:server_port")
    parser.add_argument("-i" , type=str, help="the interface the proxy will run from")
    parser.add_argument("--host", type=str, help="proxy ip address")
    parser.add_argument("--port", type=int, help="proxy port number")
    parser.add_argument("--code", type=str, help="proxy secret lock code")
    args = parser.parse_args()
    # Create proxy object
    try:
        server_addr = args.server
        server_addr = (server_addr.split(":")[0], int(server_addr.split(":")[1]))
    except:
        server_addr = None
    proxy = Proxy(host=args.host,port=args.port, server_address=server_addr, secret_code=args.code, interface=args.i)

    # Start proxy
    proxy.mainloop()
    
if __name__ == '__main__':
    main()