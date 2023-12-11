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
        messages_to_send = []

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

            messages_to_send = self.send_waiting_messages(write_socks, messages_to_send)
    
    @staticmethod
    def handle(data) -> str:
        print(f"Proxy: <{data}>")
        return data

    @staticmethod
    def send_waiting_messages(wlist:list, messages_to_send:list)->list:
        """
        Sending messages waiting messages to socket they are ready
        params: 
        wlist - list of the writeable sockets
        messages_to_send - lists that each cell contains destination socket and message encoded data
        return:
        a list of the messages that weren't sent yet 
        """
        for msg in messages_to_send:
            sock, data = msg
            if sock in wlist:
                sock.send(data)
                messages_to_send.remove(msg)
        return  messages_to_send
    
def main():
    # Create server object
    server = Server()

    # Start server
    server.start()

if __name__ == '__main__':
    main()
