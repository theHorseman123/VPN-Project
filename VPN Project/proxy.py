import socket as sock
import scapy.all
from select import select
from _thread import start_new_thread

SOCKS_VER = 5

class Proxy:

    def __init__(self, host:str="127.0.0.1", port:int=8080) -> None:
        """
        Proxy's constructor
        params: 
        self variables
        host - Proxy ip address
        port - Proxy port number
        """
        self.host = host
        self.port = port

        self.allowed_clients = [('username', 'password')]
        
    
    def get_available_methods(self, nmethods, connection):
        methods = []
        for _ in range(nmethods):
            methods.append(ord(connection.recv(1)))
        return methods

    def verify_info(self, client_sock):
        try:
            version = ord(client_sock.recv(1))

            idlen = ord(client_sock.recv(1))
            id = client_sock.recv(idlen).decode('utf-8')

            pwlen = ord(client_sock.recv(1))
            pw = client_sock.recv(pwlen).decode('utf-8')

            auth = (id, pw)

            if auth not in self.allowed_clients:
                return 1
            
            return 0
            

        except sock.error as error:
            raise error
            return 1

    def packets_exchange(self, web_sock, client_sock):

        web_sock.setblocking(False)
        client_sock.setblocking(False)

        while 1:
            try: 

                try:
                    data = client_sock.recv(4096)
                    web_sock.sendall(data)
                except BlockingIOError:
                    pass 

                try:
                    data = web_sock.recv(4096)
                    client_sock.sendall(data)
                except BlockingIOError:
                    pass

            except sock.error as error:
                break

    def client_handler(self, client_sock: sock, addr:tuple):
        """
        Handle client's request
        params:
        self variables
        client_sock- client's socket
        addr- client's address: (ip, port)
        """
        
        ver, nauth = client_sock.recv(2)
        # unsupported version
        if ver != SOCKS_VER:
            return
        
        methods = []

        for _ in range(nauth):
            methods.append(ord(client_sock.recv(1)))

        # if the client doesn't authenticate using username and password close connection
        if 2 not in methods:
            return 
        
        client_sock.sendall(bytes([SOCKS_VER, 2]))

        status = self.verify_info(client_sock)

        if status != 0:
            client_sock.sendall(bytes([1, status]))
            client_sock.close()
            return
        
        client_sock.sendall(bytes([1, status]))

        error = None

        ver, cmd, _, type = client_sock.recv(4)
        if type == 1:
            web_host = sock.inet_ntoa(client_sock.recv(4))
        elif type == 3:
            domain_length = client_sock.recv(1)[0]
            domain = client_sock.recv(domain_length)
            web_host = sock.gethostbyname(domain)
        else:
            error = 8 # address type not supported
        port = int.from_bytes(client_sock.recv(2), 'big', signed=False)
        
        if cmd == 1:
            try:
                web_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
                web_sock.connect((web_host, port))
                bind_address = web_sock.getsockname()
                print(f"# Connected to {web_host}:{str(port)}")

            except sock.error as exception:
                raise exception
                error == 5 # connection refused by destination host

        else:
            error = 7 # command not supported 

        if error:
            # send error reply
            client_sock.sendall(bytes([SOCKS_VER.to_bytes(1, 'big')]
                            , int(error).to_bytes(1, 'big') # error type
                            , int(0).to_bytes(1, 'big')
                            , int(0).to_bytes(1, 'big') # type: none
                            , int(0).to_bytes(1, 'big')
                            , int(0).to_bytes(2, 'big')))
            return
        
        host = int.from_bytes(sock.inet_aton(bind_address[0]), 'big', signed=False)
        port = bind_address[1]
        
        client_sock.sendall(b''.join([int(SOCKS_VER).to_bytes(1, 'big')
                            , int(0).to_bytes(1, 'big') # request granted
                            , int(0).to_bytes(1, 'big')
                            , int(1).to_bytes(1, 'big') # type: IPv4
                            , host.to_bytes(4, 'big')
                            , port.to_bytes(2, 'big')]))
        
        self.packets_exchange(web_sock, client_sock)

        web_sock.close()
        client_sock.close()
      
    def mainloop(self):
        """
        Proxy's mainloop which accepts new clients
        params:
        self variables
        """
        proxy_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        proxy_sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        try:
            proxy_sock.bind((self.host, self.port))
            proxy_sock.listen(5)
            print(f"# Starting proxy server: {self.host}:{str(self.port)}")
            while 1:
                client_sock, addr = proxy_sock.accept()
                print(f"# New connection from: {addr[0]}:{addr[1]}")
                start_new_thread(self.client_handler, (client_sock, addr))

        except Exception as error:
            raise error

    def notify_server(self, server_ip = "localhost", server_port = 1234):
        """
        notify the server of the proxy's activity
        params:
        self variables
        server_ip - server's ip address
        server_port - server's port number 
        """
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
    proxy.mainloop()
    
if __name__ == '__main__':
    main()
