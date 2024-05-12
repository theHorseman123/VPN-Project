import socket as sock
import os
from _thread import start_new_thread
import re
import rsa
from database import Proxies
from ..network_utils.sockets import send_message, receive_message

SECRET_CODE = "secret-horseman-NMEX123"

class Server:
    def __init__(self, host:str = "localhost", port:int=1234) -> None:
        self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.__server_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.__public_key, self.__private_key = self.__generate_keys(1024)

        self.__proxies = []

        self.__host = host
        self.__port = port

        # self.__clients_database = Clients()
        self.__proxies_database = Proxies()

    @staticmethod
    def __generate_keys(SIZE):
        # if one of the keys is missing, generate new ones
        if os.path.isfile("./auth server/public.pem") and os.path.isfile("./auth server/private.pem"):
            # TODO: write a key check to see if the encryption key is valid

            with open("auth server/public.pem", "rb") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read())

            with open("auth server/private.pem", "rb") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read())
        else:

            public_key, private_key = rsa.newkeys(SIZE)

            with open("auth server/public.pem", "wb") as f:
                f.write(public_key.save_pkcs1("PEM"))

            with open("auth server/private.pem", "wb") as f:
                f.write(private_key.save_pkcs1("PEM"))
        
        return public_key, private_key
    
    def __client_handler(self, client_socket, client_address) -> None:
        send_message(client_socket, self.__public_key.save_pkcs1("PEM")) # sends the server public key 
        data = receive_message(client_socket, 1024) # recieves the client public key 

        if not data:
            return
        
        # TODO: verify key validity
        client_key = rsa.PublicKey.load_pkcs1(data)

        # TODO: error exception
        while 1:
            data = receive_message(client_socket, 1024, self.__private_key)

            if not data:
                return
            
            data = self.__msg_handler(data) 
            
            if data:
                send_message(client_socket, data, client_key)
             
    def __msg_handler(self, msg, addr):
        data = msg.split("//")
        if len(data) != 2: # a request should have: request_type//data
            return "insuf info" 

        function = data[0]
        if (function) not in ("register", "login", "get_proxies", "update_proxy", "new_proxy"):
            return None
        
        if (function) in ("update_proxy", "new_proxy"):
            pass # TODO: symmetric decryption using the secret code

        data = data[1].split("/")
        
        try:
            msg = eval(f"self.{function}(data, addr)")
        except TypeError as error:
            print(f"error in message handel: {str(error)}")
            return
        
        return msg

    def get_proxies(self, data, addr):
        # proxies: proxies_list//addr/locked(1/0)//addr/locked(1/0)...
        proxies = self.__proxies_database.get_active_proxies()
        msg = "proxies_list"
        for proxy in proxies:
            msg+=f"//{proxy[0]}/{proxy[1]}"

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
                
    def start(self) -> None:
        # bind socket to address 
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(5)

        print("Starting server on:", (self.__host, self.__port))
        
        # TODO: add error managment
        while 1:
            client, addr = self.__server_socket.accept()
            print("* new connection at:", addr)
            # TODO: add thread limiter
            start_new_thread(self.__client_handler(client, addr))

    
def main():
    server = Server()
    server.start()

if __name__ == '__main__':
    main()
