import winreg
import sys
from _thread import start_new_thread
from ..network_utils.sockets import *
from cryptography.fernet import Fernet
import os
import rsa


root = winreg.HKEY_CURRENT_USER
reg_key = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


class Client:
    def __init__(self, host = "localhost", port = 0, username=None, password=None):

        self.__host = host
        self.__port = port

        self.__server_socket = None
        self.__server_public_key = None

        self.__username = username
        self.__password = password

        self.__active_proxies = []

        self.__public_key, self.__private_key = self.__generate_keys(1024)

    def get_proxies(self):
        if not self.__server_socket:
            return "No VPN server connected"
        
        send_message(self.__server_socket, "get_proxies//", self.__server_public_key)
        
        if not data:
            return

        data = receive_message(self.__server_socket, 1024, self.__private_key)
        
        if not data:
            return
        
        data = data.split("//")
        if not len(data) > 1:
            return "No proxies returned"
        data = data[0:]
        self.__active_proxies = list(map(lambda x: x.split("/"), data.split("//")))
        return self.__active_proxies
    
    @staticmethod
    def __generate_keys(SIZE):
        # if one of the keys is missing, generate new ones
        if os.path.isfile("./vpn client/public.pem") and os.path.isfile("./auth server/private.pem"):
            # TODO: write a key check to see if the encryption key is valid

            with open("vpn client/public.pem", "rb") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read())

            with open("vpn client/private.pem", "rb") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read())
            
        
        else:

            public_key, private_key = rsa.newkeys(SIZE)

            with open("vpn client/public.pem", "wb") as f:
                f.write(public_key.save_pkcs1("PEM"))

            with open("vpn client/private.pem", "wb") as f:
                f.write(private_key.save_pkcs1("PEM"))
        
        return public_key, private_key

    def __connect_to_proxy(self, addr):
        proxy_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

        proxy_socket.connect(addr)

        # TODO: error management
        
        # Exchange asymetric keys

        data_recived = proxy_socket.recv(1024)
        
        if data_recived == "":
            return
        
        proxy_public_key = rsa.PublicKey.load_pkcs1(data_recived)

        proxy_socket.sendall(self.__public_key.save_pkcs1("PEM"))

    def connect_server(self, server_address):
        
        self.__server_socket = connect_to_destination(server_address)
        if not self.__server_socket: # couldnt connect to server
            return
        
        data = self.__receive_message(self.__server_socket, 1024)
        
        if not data:
            return
        
        self.__server_public_key = rsa.PublicKey.load_pkcs1(data)

        send_message(self.__server_socket, self.__public_key.save_pkcs1("PEM"))


def main():
    # Create server object
    client = Client()
    client.connect_server(("localhost",  1234))

if __name__ == '__main__':
    main()
