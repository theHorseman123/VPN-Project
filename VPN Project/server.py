import socket as sock
from _thread import start_new_thread
from select import select
import re


class Server:
    def __init__(self, host:str = sock.gethostbyname(sock.gethostname())[0], port:int=1234) -> None:
        self.sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.proxies = []

        self.host = host
        self.port = port

    @staticmethod
    def get_active_proxies():
        pass
    
    def handler(self, sock, data) -> None:
        data = data.split('/')
        # If the function is not included in the functions offered
        if data[0] not in ("get", "proxy"):
            return
        msg = None
        try:
            # calls the right function based on the data given
            return eval("self."+data[0]+"(data, sock)")
        except SyntaxError:
            pass
    
    def proxy(self, data, sock):
        host = data[1]
        port = int(data[2])

        # filter out illegal port number/ ip address
        if not re.match("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", host) or port > 65535 or port < 1:
            return "illegal"
        # checks if the proxy already exists
        if (host, port) in self.proxies:
            return "dupe"
        
        print("New proxy connected at:", (host, port))
        self.proxies.append((host, port))
        return "pass"

    def get(self, data, sock):
        msg = "get"
        for proxy in self.proxies:
            msg += f"/{proxy[0]}/{proxy[1]}"
        
        return msg

    def start(self) -> None:
        # bind socket to address 
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)

        rlist = []

        print("Starting server on:", (self.host, self.port))
        
        messages_to_send = []
        while 1:
            # get readable and writeable socket 
            read_socks, write_socks, _ = select(rlist+[self.sock], rlist, [])
            for read_sock in read_socks:
                try:
                    # if a new client tries to connect
                    if read_sock is self.sock:
                        sock, addr = read_sock.accept()
                        print("\nNew connection from: ", (addr))
                        rlist.append(sock)
                        continue
                    
                    data = read_sock.recv(1024)
                    if data:
                        msg = self.handler(read_sock, data.decode('utf-8'))
                        if msg:
                            messages_to_send.append((msg.encode('utf-8'), read_sock))
                    else:
                        print(f"Closing connection with: {read_sock.getpeername()}")
                        rlist.remove(read_sock)
                        read_sock.close()
                except ConnectionResetError as error:
                    print(f"Closing communication with: {read_sock.getpeername()}")
                    rlist.remove(read_sock)
                    read_sock.close()

            
            # send waiting messages to clients that are ready to receive
            for message in messages_to_send:
                sock = message[1]
                msg = message[0]
                if sock in write_socks:
                    sock.send(msg)     
                    messages_to_send.remove(message)
        
    
    
def main():
    # Create server object
    server = Server()

    # Start server
    server.start()

if __name__ == '__main__':
    main()
