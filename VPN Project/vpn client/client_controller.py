import winreg as reg
import sys
import socket as sock
from select import select
from _thread import start_new_thread
from cryptography.fernet import Fernet
import os
import rsa
import pydivert

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.cryptography import *


def enable_proxy():
    # this function sends the user traffic to localhost:5555  
    internet_settings = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
    
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, internet_settings, 0, reg.KEY_SET_VALUE) as key:
            # Set the proxy server to the specified address
            reg.SetValueEx(key, 'ProxyServer', 0, reg.REG_SZ, "localhost:5555")
            # Enable the proxy by setting the ProxyEnable value to 1
            reg.SetValueEx(key, 'ProxyEnable', 0, reg.REG_DWORD, 1)
            
            print(f' *Proxy settings updated: localhost:5555')
            return True
        
    except Exception as error:
        print(f' ERROR: {str(error)}')
    return False

def disable_proxy():
    # Path to the registry key
    internet_settings = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
    
    try:
        # Connect to the registry and open the key
        with reg.OpenKey(reg.HKEY_CURRENT_USER, internet_settings, 0, reg.KEY_SET_VALUE) as key:
            # Disable the proxy by setting the ProxyEnable value to 0
            reg.SetValueEx(key, 'ProxyEnable', 0, reg.REG_DWORD, 0)
            
            print(' *Proxy has been disabled.')
            return True
    except Exception as error:
        print(f' ERROR: {str(error)}')
    return False

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



class Client:
    def __init__(self, host = "localhost", port = 0, server_address=("localhost", 1234)):

        self.__host = host
        self.__port = port

        self.__server_address = (server_address)
        self.__server_socket = None

        self.__active_proxies = []

        self.__server_key = aes_generate_key()

        self.__public_key, self.__private_key = generate_keys(1024, "vpn client")

    def start_client(self):

        status = self.__connect_server()
        if not status:
            return
        
        status = self.__get_proxies()
        if not status:
            return
        proxies = self.__active_proxies[0]
        proxy_address = proxies[0]
        status = self.__get_proxy_key(proxy_address)
        
        if not status[1]:
            print(status[0])
            return
        proxy_public = status[0]
        proxy_address = proxy_address.split(":")
        proxy_address = (proxy_address[0], int(proxy_address[1]))

        while 1:
            status = self.__connect_to_proxy(proxy_address, proxy_public)
            if not status[1]:
                print(status[0])
                return
            
            proxy_socket, proxy_key = status[0] # socket to communicate on and a symmetric key
            
            self.__start_outer_client(proxy_key, proxy_socket)
        
    def __get_proxy_key(self, proxy_addr):
        # return: wanted proxy public key and True/False
        data = (f"get_proxy_key//{proxy_addr}").encode()
        encrypted_data = self.__server_key.encrypt(data)
        
        send(self.__server_socket, encrypted_data)
        
        encrypted_data = receive(self.__server_socket)
        if not data:
            return " INFO: Server disconnected", False
        data = self.__server_key.decrypt(encrypted_data)

        if data == b"not_found":
            return " INFO: Proxy not found", False
        return rsa.PublicKey.load_pkcs1(data), True

    def __get_proxies(self):
        if not self.__server_socket:
            return "No VPN server connected"
        data = b"get_proxies//"
        encrypted_data = self.__server_key.encrypt(data)
        send(self.__server_socket, encrypted_data)
        encrypted_data = receive(self.__server_socket)
        if not encrypted_data:
            return
        
        data = self.__server_key.decrypt(encrypted_data).decode()
        print(data)
        data = data.split("//")
        
        data = data[1:]
        self.__active_proxies = list(map(lambda x: x.split("|"), data))
        return self.__active_proxies

    def __connect_to_proxy(self, proxy_address, proxy_public):
        try:
            proxy_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            proxy_socket.connect(proxy_address)

            data = receive(proxy_socket)
            
            if not data:
                return " INFO: Proxy left", False
            
            if data == b"secret_code_required":
                secret_code = input(f"{proxy_address[0]}:{str(proxy_address[1])} is asking for a code, please insert: ")
                encrypted_code = rsa_encrypt_message(secret_code, proxy_public)
                send(proxy_socket, encrypted_code)
                status = receive(proxy_socket)
                
                if not status:
                    return " INFO: Proxy left", False
                if status == b"wrong_key":
                    return " INFO: Wrong code proxy left", False
            
            proxy_key = aes_generate_key()
            data = aes_retreive_key(proxy_key)
            encrypted_data = rsa_encrypt_message(data.decode(), proxy_public)
            
            send(proxy_socket, encrypted_data)

            return (proxy_socket, proxy_key), True
        
        except sock.error as error:
            proxy_socket.close()
            return f" Error:{str(error)}", False
        
    def __connect_server(self):
        try:
            self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.__server_socket.connect((self.__server_address))
        except sock.error as error:
            print(f"couldn't connect to the server: {str(error)}")
        
        data = receive(self.__server_socket)
        
        if not data:
            print(" INFO: server disconnected")
            return
        
        server_public_key = rsa.PublicKey.load_pkcs1(data)

        data = aes_retreive_key(self.__server_key).decode()
        encrypted_data = rsa_encrypt_message(data, server_public_key)
        
        send(self.__server_socket, encrypted_data)
        encrypted_data = receive(self.__server_socket)

        if not data:
            return

        data = self.__server_key.decrypt(encrypted_data)
        if data == b"pass":
            return "pass"

    def __start_outer_client(self, proxy_key, proxy_socket):
        try:
            server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.__server_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
            server_socket.bind(("localhost", 5555))
            server_socket.listen(5)
            
            enable_proxy()

            proxy_socket.setblocking(False)

        except sock.error as error:
            print(f"ERROR: {str(error)}")
            return
        print(" *Starting server on", (server_socket.getsockname()))
        try:    
            while 1:
                if not proxy_socket:
                    print(f" INFO: Proxy left")
                    print(" *Disabling proxy")
                    disable_proxy()
                    return 

                socket, addr = server_socket.accept()
                start_new_thread(self.__request_handler, (socket, proxy_socket, proxy_key))

        except sock.error as error:
            print(f" ERROR: {str(error)}")
            print(" *Disabling proxy")
            disable_proxy()
            proxy_socket.close()     

    def __request_handler(self, socket:sock, proxy_socket:sock, proxy_key):
        socket.setblocking(False)
        readlist = [socket, proxy_socket]
        
        while 1:
            try:
                read_sockets, _, _ = select(readlist, [], [])
                for read_socket in read_sockets:
                    if read_socket is socket:
                        data = socket.recv(4096)
                        print(data)
                        if data == b"":
                            socket.close()
                            return

                        encrypted_data = proxy_key.encrypt(data)
                        send(proxy_socket, encrypted_data)


                    else:
                        encrypted_data = receive(proxy_socket)
                    
                        if not encrypted_data:
                            proxy_socket.close()
                            socket.close()
                            return
                        
                        data = proxy_key.decrypt(data)
                        print(data)
                        socket.sendall(data.encode("utf-8"))
            except:
                socket.close()
                return


def main():
    # Create server object
    client = Client()
    client.start_client()

if __name__ == '__main__':
    main()