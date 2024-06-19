import socket as sock
from scapy.all import get_if_addr
import argparse
import os
from _thread import start_new_thread
import rsa
# from database import Proxies
import sys
from logger import Logger

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.cryptography import *

PROXY_SECRET_KEY = aes_generate_key("secret-horseman-NMEX123")


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
        
        if not msg_fragment:
            print(" INFO: socket has discconected at:", (socket.getpeername()))
            return 
        message = message + msg_fragment
    return message


class Server:
    def __init__(self, host:str = None, port:int=None, interface=None) -> None:
        
        self.logger = Logger()

        if interface:
            if not host:
                try:
                    host = get_if_addr(interface)
                except Exception as error:
                    raise error
        if not host:
            host = "localhost"
        if not port:
            port = 1234
        
        self.__server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.__server_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.__public_key, self.__private_key = generate_keys(1024)

        self.__active_proxies = {}

        self.__host = host
        self.__port = port

        # self.__clients_database = Clients()
        # self.__proxies_database = Proxies()
        
    def __client_handler(self, client_socket, client_address) -> None:
        try:
            send(client_socket, self.__public_key.save_pkcs1("PEM"))
            encrypted_data = receive(client_socket) # recieves the client symmetric key 
            if not encrypted_data:
                client_socket.close()
                return
            try:
                key = rsa_decrypt_message(encrypted_data, self.__private_key)
                client_key = Fernet(key)
                encrypted_data = client_key.encrypt(b"pass")
                send(client_socket, encrypted_data)
            except ValueError:
                print(" INFO: Client supplied a non valid key")
                data = b"no key suplied"
                send(client_socket, data)
                print(" *Closing connection with:", client_address)
                self.logger.write(f" *Closing connection with: {client_address[0]}:{str(client_address[1])}")
                client_socket.close()

            while 1:
                    encrypted_data = receive(client_socket)

                    if not encrypted_data:
                        self.__close_connection(client_socket)
                        return
                    
                    data = client_key.decrypt(encrypted_data)
                    
                    data = self.__msg_handler(data.decode(), client_socket)
                    
                    if data:
                        encrypted_data = client_key.encrypt(data.encode())
                        send(client_socket, encrypted_data)
        
        except Exception as error:
            print(f"ERROR: {error}")
            self.__close_connection(client_socket)
            return
    
    def __close_connection(self, socket):
        if socket.getpeername() in list(self.__active_proxies.keys()):
            print(" *Closing connection with proxy:", (socket.getpeername()))
            self.logger.write(f" *Closing connection with proxy: {socket.getpeername()[0]}: {str(socket.getpeername()[1])}")
            del self.__active_proxies[self.__active_proxies[socket.getpeername()]]
        else:
            print(" *Closing connectiong with client:", (socket.getpeername()))
            self.logger.write(f" *Closing connectiong with client:{socket.getpeername()[0]}: {str(socket.getpeername()[1])}")
        socket.close()

    def __msg_handler(self, msg, socket):
        data = msg.split("//")
        if len(data) != 2: # a request should have: request_type//data
            return "insuf info" 

        function, data = data

        if (function) not in ("get_proxies", "new_proxy", "get_proxy_key"):
            return "function_not_found"
        
        if (function) in ("new_proxy", ):
            # To create a proxy you need a special key to authenticate you are trustworthy
            data = PROXY_SECRET_KEY.decrypt(data).decode()
            
        data = data.split("|")
        
        try:
            msg = eval(f"self.{function}(data, socket)")
        except TypeError as error:
            print(f"ERROR: {str(error)}")
            return
        
        return msg

    def get_proxies(self, data, socket):
        # proxies: proxies_list//addr/locked(1/0)//addr/locked(1/0)...
        msg = "proxies_list"
        for address, lock_status in self.__active_proxies.items():
            msg+=f"//{address}|{lock_status[0]}"
        return msg

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

    def get_proxy_key(self, data, socket):
        # return: publickey | data: proxy ipaddr:port
        proxy_address = data[0]
        try:
            public_key = self.__active_proxies[proxy_address][1]
            return public_key.save_pkcs1("PEM").decode()
        except AttributeError:
            del self.__active_proxies[proxy_address]
        except:
            pass
        return "not_found"

    def new_proxy(self, data, socket):
        # new proxy data: locked(1/0)/proxy publickey  
        if len(data) == 3:
            try:
                if not data[0] in self.__active_proxies.keys():
                    self.__active_proxies.update({data[0]: (data[1], rsa.PublicKey.load_pkcs1(data[2]))})
                    self.__proxy_sockets = {socket: data[0]}
                    print(" INFO: New proxy connected from", (socket.getpeername()))
                    self.logger.write(f" INFO: New proxy connected from: {(socket.getpeername())[0]}:{str(socket.getpeername()[1])}")
                    return "pass"
                else:
                    return "address already exists in the network"
            except AttributeError as error:
                print(f"ERROR: {str(error)}")
                return "invalid_key"
        return "wrong_input"

    def start(self) -> None:
        # bind socket to address 
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(5)

        print(" *Starting server on:", (self.__host, self.__port))
        
        while 1:
            try:
                client, addr = self.__server_socket.accept()
                print(" INFO: new connection at:", addr)
                self.logger.write(f" INFO: new connection at: {addr[0]}:{str(addr[1])}")
                start_new_thread(self.__client_handler, (client, addr))
            except Exception as error:
                print(f" ERROR: {error}")
    
def main():
    parser = argparse.ArgumentParser(description='This is the code for the VPN server')
    parser.add_argument("-i" , type=str, help="the interface the server will run from")
    parser.add_argument("--host", type=str, help="VPN server ip address")
    parser.add_argument("--port", type=int, help="VPN server port number")
    args = parser.parse_args()
    server = Server(host=args.host, port=args.port, interface=args.i)
    server.start()

if __name__ == '__main__':
    main()