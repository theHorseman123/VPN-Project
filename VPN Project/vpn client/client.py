import socket as sock
import winreg
import sys
from _thread import start_new_thread
import os
import rsa


root = winreg.HKEY_CURRENT_USER
reg_key = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


class Client:
    def __init__(self, host = "localhost", port = 0, username=None, password=None):

        self.__host = host
        self.__port = port

        self.__username = username
        self.__password = password

        self.__public_key, self.__private_key = self.__generate_keys(1024)


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

    def __connect_proxy(self):
        pass

    def connect_server(self, addr):
        server = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

        server.connect(addr)
        
        # TODO: error management
        data = server.recv(1024)
        
        if data == "":
            return
        
        server_key = rsa.PublicKey.load_pkcs1(data)

        server.sendall(self.__public_key.save_pkcs1("PEM"))
        while 1:
            data = input().encode('utf-8')
            msg = rsa.encrypt(data, server_key)
            server.send(msg)

            data = server.recv(1024)
            if data == "":
                return
            print(rsa.decrypt(data, self.__private_key).decode('utf-8'))
            
            
def main():
    # Create server object
    client = Client()
    client.connect_server(("localhost",  1234))

if __name__ == '__main__':
    main()