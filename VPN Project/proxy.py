import socket as sock
import scapy.all
from select import select
from _thread import start_new_thread


class Proxy:

    def __init__(self, host="127.0.0.1", port=8080) -> None:
        self.host = host
        self.port = port

    def client_handler(self, client_sock, addr):
        while 1:
            request = client_sock.recv(1024)
            print(request)

    def mainloop(self):
        proxy_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        proxy_sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        try:
            proxy_sock.bind((self.host, self.port))
            proxy_sock.listen(5)
            while 1:
                print("Starting proxy server")
                client_sock, addr = proxy_sock.accept()
                print("New connection from:",(addr))
                start_new_thread(self.client_handler, (client_sock, addr))

        except Exception as error:
            raise error

    def notify_server(self, server_ip = "localhost", server_port = 1234):
        
        sock_proxy = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        sock_proxy.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        try:
            print()
            sock_proxy.bind((server_ip, 0))
            sock_proxy.connect((server_ip, server_port))
            print("connection established with server at:", (server_ip, server_port))
            
            sock_proxy.send(f"proxy/{self.host}/{self.port}".encode('utf-8'))
            data = sock_proxy.recv(1024)
            if not data == b"illegal" and not data == b"":
                print("notified successfully")
                sock_proxy.close()

            else:
                print("The server is offline")
                sock_proxy.close()

        except Exception as error:
            sock_proxy.close()
            raise error

def main():
    # Create proxy object
    proxy = Proxy()

    # Start proxy
    proxy.notify_server()
    proxy.mainloop()
    
if __name__ == '__main__':
    main()
