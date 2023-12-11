import socket as sock
from select import select


class Server:
    def __init__(self, host:str = "localhost", port:int=1234) -> None:
        self.sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        self.host = host
        self.port = port

    def start(self) -> None:
        # bind socket to address 
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)

        rlist = []

        print("Starting server on:", (self.host, self.port))
        
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
                        print(f"Proxy: <{data.decode('utf-8')}>")
                        read_sock.send(data)
                    else:
                        print(f"Closing connection with: {read_sock.getpeername()}")
                        rlist.remove(read_sock)
                        read_sock.close()
                
                except Exception as error:
                    print(error)
                    print(f"Closing connection with: {read_sock.getpeername()}")
                    rlist.remove(read_sock)
                    read_sock.close()
    
    
def main():
    # Create server object
    server = Server()

    # Start server
    server.start()

if __name__ == '__main__':
    main()
