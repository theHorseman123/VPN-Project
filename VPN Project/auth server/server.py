import socket as sock
import os
from _thread import start_new_thread
import re
import rsa
# from database import Proxies
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.cryptography import *

SECRET_CODE = "secret-horseman-NMEX123"


def send(socket, data):
    try:
        socket.send(str(len(data)).zfill(8).encode() + data)
    except sock.error as error:
        print(f"socket error: {str(error)}")

def receive(socket:sock):
    try:
        message_size = socket.recv(8)
    except sock.error as error:
        print(f"socket error: {str(error)}")
        return 
    if not message_size:
        print(f"server disconnected")
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
            print(msg_fragment)
        except sock.error as error:
            print(f"socket error: {str(error)}")
            return 
        
        if not msg_fragment:
            print("server has discconected")
            return 
        message = message + msg_fragment
    
    print(message)
    return message


class Server:
    def __init__(self, host:str = "localhost", port:int=1234) -> None:
        self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.__server_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.__public_key, self.__private_key = generate_keys(1024, "auth server")

        self.__active_proxies = {}

        self.__host = host
        self.__port = port

        # self.__clients_database = Clients()
        # self.__proxies_database = Proxies()
        
    def __client_handler(self, client_socket, client_address) -> None:
        send(client_socket, self.__public_key.save_pkcs1("PEM"))
        data = receive(client_socket) # recieves the client public key 
        if not data:
            return
        
        # TODO: verify key validity
        client_key = rsa.PublicKey.load_pkcs1(data)

        # TODO: error exception
        while 1:
            encrypted_data = receive(client_socket)
            data = rsa_decrypt_message(encrypted_data, self.__private_key)

            if not data:
                return
            
            data = self.__msg_handler(data, client_address)
            
            if data:
                encrypted_data = rsa_encrypt_message(data, client_key)
                send(client_socket, encrypted_data)
             
    def __msg_handler(self, msg, addr):
        data = msg.split("//")
        if len(data) != 2: # a request should have: request_type//data
            return "insuf info" 

        function = data[0]
        if (function) not in ("get_proxies", "new_proxy", "get_proxy_key"):
            return "function_not_found"
        
        """
        if (function) in ("update_proxy", "new_proxy"):
            pass # TODO: symmetric decryption using the secret code
        """

        data = data[1].split("/")
        
        try:
            msg = eval(f"self.{function}(data, addr)")
        except TypeError as error:
            print(f"error in message handel: {str(error)}")
            return
        
        return msg

    def get_proxies(self, data, addr):
        # proxies: proxies_list//addr/locked(1/0)//addr/locked(1/0)...
        msg = "proxies_list"
        for addr, lock_status in self.__active_proxies.items():
            msg+=f"//{addr}/{lock_status}"

    """
    def update_proxy(self, data, addr):
        # update proxy: update//user/password/(lock code) -> updates activity and new port&ipaddr
        if len(data) == 2: # update proxy activity
            return self.__proxies_database.update_active_proxy((data[0], data[1], f"{addr[0]}:{str(addr[1])}"))
        
        elif len(data) == 3: # update lock code for proxy
            return self.__proxies_database.update_active_proxy((data[0], data[1], data[2],  f"{addr[0]}:{str(addr[1])}"))                
    
    def new_proxy(self, data, addr):
        # new proxy: new_proxy//user/password/(code)
        if len(data) == 2: # new proxy with no code
            return self.__proxies_database.new_proxy((data[0], data[1], f"{addr[0]}:{str(addr[1])}"))
        
        elif len(data) == 3: # lock code for proxy
            return self.__proxies_database.new_proxy((data[0], data[1], data[2],  f"{addr[0]}:{str(addr[1])}"))
    """    

    def get_proxy_key(self, data, addr):
        # return: publickey | data: proxy ipaddr:port
        addr = data.split(":")
        try:
            public_key = self.__active_proxies[addr][1]
            return public_key.save_pkcs1("PEM")
        except AttributeError:
            del self.__active_proxies(addr)
        except:
            pass
        return "not_found"

    def new_proxy(self, data, addr):
        # new proxy data: locked(1/0)/proxy publickey  
        if len(data) == 1:
            try:
                self.__active_proxies.update({addr:(data[0],rsa.PublicKey.load_pkcs1(data[1]))})
                print(" INFO: New proxy connected from", (addr))
                return "pass"
            except AttributeError:
                return "invalid_key"
        return "wrong_input"

    def start(self) -> None:
        # bind socket to address 
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(5)

        print(" *Starting server on:", (self.__host, self.__port))
        
        # TODO: add error managment
        while 1:
            client, addr = self.__server_socket.accept()
            print(" INFO: new connection at:", addr)
            # TODO: add thread limiter
            start_new_thread(self.__client_handler, (client, addr))

    
def main():
    server = Server()
    server.start()

if __name__ == '__main__':
    main()