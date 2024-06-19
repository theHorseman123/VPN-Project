import winreg as reg
import sys
import socket as sock
from select import select
from _thread import start_new_thread
import threading
from cryptography.fernet import Fernet
import os
import rsa
from scapy.all import get_if_addr
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.cryptography import *


def enable_proxy(addr):
    # this function sends the user traffic to localhost:5555  
    internet_settings = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
    
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, internet_settings, 0, reg.KEY_SET_VALUE) as key:
            # Set the proxy server to the specified address
            reg.SetValueEx(key, 'ProxyServer', 0, reg.REG_SZ, addr)
            # Enable the proxy by setting the ProxyEnable value to 1
            reg.SetValueEx(key, 'ProxyEnable', 0, reg.REG_DWORD, 1)
            
            print(f' *Proxy settings updated: {addr}')
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
        print(" INFO: socket has disconnected at:", (socket.getpeername()))
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
            print(" INFO: socket has disconnected at:", (socket.getpeername()))
            return 
        message = message + msg_fragment
    return message

class Client:
    def __init__(self, interface=None, server_address=None):
        if interface:
            if not server_address:
                server_address = (get_if_addr(interface), 1234)
        
        if not server_address:
            server_address = ("localhost", 1234)

        self.server_address = server_address
        self.__server_socket = None

        self.proxies_speed = {} # connected proxies speed: {proxy address: [proxy_speed1, proxy_speed2, .. proxy_speed30]}
        
        # [(proxy address, proxy_key, session id, secret code/None, proxy public key, proxy disconnected event, client disconnect event), (proxy2), (proxy3), ..]
        self.proxies_connections = []

        self.__active_proxies = []

        self.__server_key = aes_generate_key()

        self.console = None

    """
    def add_connection(self, proxy_addr, event:threading.Event, secret_code=None):
        status = self.get_proxy_key(proxy_addr)

        if not status[1]:
            self.console.write(status[0])
            return False
        self.console.write(f" INFO: Connected to proxy at: {proxy_addr}")
        proxy_address = (proxy_addr.split(":")[0], int(proxy_addr.split(":")[1]))
        proxy_public = status[0]
    """

    def app_proxy_connect(self, proxy_addr, console, event:threading.Event, disconnect, secret_code=None):
        status = self.get_proxy_key(proxy_addr)

        if not status[1]:
            console.write(status[0])
            return False

        console.write(f" INFO: Connected to proxy at: {proxy_addr}")
        proxy_address = (proxy_addr.split(":")[0], int(proxy_addr.split(":")[1]))
        proxy_public = status[0]

        status = self.__connect_to_proxy(proxy_address=proxy_address, proxy_public=proxy_public, secret_code=secret_code)
        if not status[1]:
            self.console.write(f" INFO: can not connect to proxy: {status[0]}")
            return
        proxy_socket, proxy_key, session_id = status[0]
        proxy_offline = threading.Event()
        # [(proxy address, proxy_key, session id, proxy socket, secret code/None, proxy disconnected event, client disconnect event)]
        # append proxy info to proxies connection
        self.proxies_connections.append((proxy_address, proxy_key, session_id, secret_code, proxy_public, proxy_offline, event))
        
        if not self.console: # if this is the first proxy connection
            self.console = console
            start_new_thread(self.__start_outer_client, (disconnect, ))
        
        self.proxies_speed.update({proxy_addr:[]})
        start_new_thread(self.__test_proxy_speed, (proxy_socket, proxy_address,  proxy_key, session_id, proxy_public, event, proxy_offline))

        proxy_offline.wait() # TODO: add session timeout

        return True

    def get_proxy_key(self, proxy_addr):
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

    def get_proxies(self):
        if not self.__server_socket:
            return "No VPN server connected"
        data = b"get_proxies//"
        encrypted_data = self.__server_key.encrypt(data)
        send(self.__server_socket, encrypted_data)
        encrypted_data = receive(self.__server_socket)
        if not encrypted_data:
            return "Server left"
        
        data = self.__server_key.decrypt(encrypted_data).decode()
        self.__active_proxies = [proxy.split("|") for proxy in data.split("//")][1:]
        return self.__active_proxies

    def __connect_to_proxy(self, proxy_address, proxy_public, secret_code=None, session_id=None, proxy_key=None):
        try:
            proxy_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            proxy_socket.connect(proxy_address)


            if session_id and proxy_key: # if the client already has an encrypted session with proxy
                encrypted_data = rsa_encrypt_message(session_id.decode(), proxy_public)
                send(proxy_socket, encrypted_data)
                encrypted_data = receive(proxy_socket)
                if not encrypted_data:
                    return " INFO: Proxy left", False
                
                data = proxy_key.decrypt(encrypted_data)
                if data == b"pass":
                    return (proxy_socket, proxy_key, session_id), True
            else:
                send(proxy_socket, rsa_encrypt_message("pass", proxy_public))


            data = receive(proxy_socket)
            
            if not data:
                return " INFO: Proxy left", False
            
            if data == b"secret_code_required":
                if not secret_code:
                    return " INFO: Proxy requires a code", False
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

            encrypted_data = receive(proxy_socket)
            
            if not encrypted_data:
                return " INFO: Proxy left", False
            
            session_id = proxy_key.decrypt(encrypted_data)

            return (proxy_socket, proxy_key, session_id), True
        
        except sock.error as error:
            proxy_socket.close()
            return f" Error:{str(error)}", False
        
    def connect_server(self):
        try:
            self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.__server_socket.connect((self.server_address))
        except Exception as error:
            return f" ERROR: {str(error)}"
        
        data = receive(self.__server_socket)
        
        if not data:
            return " INFO: server disconnected"
        
        server_public_key = rsa.PublicKey.load_pkcs1(data)

        data = aes_retreive_key(self.__server_key).decode()
        encrypted_data = rsa_encrypt_message(data, server_public_key)
        
        send(self.__server_socket, encrypted_data)
        encrypted_data = receive(self.__server_socket)

        if not data:
            return " INFO: server disconnected"

        data = self.__server_key.decrypt(encrypted_data)
        if data == b"pass":
            return "pass"

    def __start_outer_client(self, disconnect:threading.Event):
        outer_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        outer_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
        outer_socket.bind(("localhost", 5555))
        outer_socket.listen(5)

        enable_proxy("localhost:5555")

        while not disconnect.is_set(): # disconnect event happens when the client disconnects all proxies
            if len(self.proxies_connections) == 0:
                time.sleep(1)
            for proxy_address, proxy_key, session_id, secret_code, proxy_public, proxy_offline, client_event in self.proxies_connections:
                try:
                    if client_event.is_set():
                        proxy_offline.set()
                    
                    if proxy_offline.is_set():
                        self.proxies_connections.remove((proxy_address, proxy_key, session_id, secret_code, proxy_public, proxy_offline, client_event))

                    socket, _  = outer_socket.accept()
                    start_new_thread(self.__request_handler, (socket, proxy_address, proxy_key, session_id, secret_code, proxy_public, proxy_offline))
                
                except Exception as error:
                    self.console.write(f" ERROR:{str(error)}")
                    proxy_offline.set()
                    continue

        disable_proxy()
        self.console = None

    def __test_proxy_speed(self, proxy_socket, proxy_address,  proxy_key, session_id, proxy_public, event:threading.Event, proxy_offline:threading.Event):
        try:
            proxy_addr = f"{proxy_address[0]}:{str(proxy_address[1])}"
            while not (proxy_offline.is_set() or event.is_set()):
                encrypted_data = proxy_key.encrypt(b"CONNECT www.google.com:443\r\n\r\n")
                size = len(encrypted_data)+8
                send(proxy_socket, encrypted_data)
                initial_time = time.time_ns()
                data = receive(proxy_socket)
                if not data:
                    return
                size += len(data)+8
                finish_time = time.time_ns()
                result = size/((finish_time-initial_time)*(10**-6))
                proxy_socket.close()
                if len(self.proxies_speed[proxy_addr]) == 30:
                    self.proxies_speed[proxy_addr] = self.proxies_speed[proxy_addr][1:]
                self.proxies_speed[proxy_addr].append(result)
                proxy_socket.close()
                time.sleep(1)
                status = self.__connect_to_proxy(proxy_address=proxy_address, proxy_key=proxy_key, session_id=session_id, proxy_public=proxy_public)
                if status[1]:
                    proxy_socket, _, _ = status[0]
                else:
                    return
        except Exception as error:
            pass
        if proxy_socket is sock:
            proxy_socket.close()

    def __request_handler(self, socket:sock, proxy_address, proxy_key, session_id, secret_code, proxy_public , proxy_offline):
        status = self.__connect_to_proxy(proxy_address=proxy_address, proxy_public=proxy_public, secret_code=secret_code, session_id=session_id, proxy_key=proxy_key)
        if not status[1]:
            self.console.write(f" INFO: cant connect to proxy: {status[0]}")
            return
        
        proxy_socket, proxy_key, _ = status[0]
        
        readlist = [socket, proxy_socket]
        
        while not proxy_offline.is_set():
            try:
                read_sockets, _, _ = select(readlist, [], [])
                for read_socket in read_sockets:
                    if read_socket is socket:
                        data = socket.recv(4096)
                        if data == b"":
                            socket.close()
                            proxy_socket.close()
                            return

                        encrypted_data = proxy_key.encrypt(data)
                        send(proxy_socket, encrypted_data)


                    else:
                        encrypted_data = receive(proxy_socket)

                        if not encrypted_data:
                            proxy_offline.set()
                            socket.close()
                            proxy_socket.close()
                            return
                        data = proxy_key.decrypt(encrypted_data)
                        if data == b"close":
                            socket.close()
                            proxy_socket.close()
                            return
                        socket.sendall(data)
            except sock.error as error:
                if read_socket is proxy_socket:
                    self.console.write(str(error))
                    proxy_offline.set()
                proxy_socket.close()
                return
            
        proxy_socket.close()
        socket.close()
