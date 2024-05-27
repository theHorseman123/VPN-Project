import winreg
import pydivert
import sys
import socket as sock
from _thread import start_new_thread
from cryptography.fernet import Fernet
import os
import rsa

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.cryptography import *


root = winreg.HKEY_CURRENT_USER
reg_key = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

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
        except sock.error as error:
            print(f"socket error: {str(error)}")
            return 
        
        if not msg_fragment:
            print("server has discconected")
            return 
        message = message + msg_fragment
    print(message)
    return message

class Client:
    def __init__(self, host = "localhost", port = 0, server_address=("localhost", 1234)):

        self.__host = host
        self.__port = port

        self.__server_address = (server_address)
        self.__server_socket = None
        self.__server_public_key = None

        self.__active_proxies = []

        self.__public_key, self.__private_key = generate_keys(1024, "vpn client")

    def start_client(self):

        status = self.__connect_server()
        if not status:
            return
        
        status = self.__get_proxies()
        if not status:
            return
        return self.__active_proxies
    
    def get_proxy_key(self):
        pass

    def __get_proxies(self):
        if not self.__server_socket or not self.__server_public_key:
            return "No VPN server connected"
        print(1)
        data = "get_proxies//"
        encrypted_data = rsa_encrypt_message(data, self.__server_public_key)
        send(self.__server_socket, encrypted_data)
        print(2)
        encrypted_data = receive(self.__server_socket)
        print(3)
        print(encrypted_data)
        print(data)
        if not data:
            return
        
        data = rsa_decrypt_message(encrypted_data, )
        
        data = data.split("//")
        if not len(data) > 1:
            print(data)
            return "No proxies returned"
        
        data = data[0:]
        self.__active_proxies = list(map(lambda x: x.split("/"), data.split("//")))
        print("active proxies:", self.__active_proxies)
        return self.__active_proxies

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

    def __connect_server(self):
        try:
            self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.__server_socket.connect((self.__server_address))
        except sock.error as error:
            print(f"couldn't connect to the server: {str(error)}")
        
        data = receive(self.__server_socket)
        
        if not data:
            print("server disconnected")
            return
        
        self.__server_public_key = rsa.PublicKey.load_pkcs1(data)
        send(self.__server_socket, self.__public_key.save_pkcs1("PEM"))

        return "pass"

def main():
    # Create server object
    client = Client()
    client.start_client()

if __name__ == '__main__':
    main()