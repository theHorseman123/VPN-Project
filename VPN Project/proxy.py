from socket import *
from select import select

class Proxy:

    def __init__(self, host:str="localhost", port:int = 8080, server_host:str ="localhost", server_port:int=1234) -> None:
        
        self.proxy = socket(AF_INET, SOCK_STREAM)
        self.proxy.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.host = host
        self.port = port

        self.server_host = server_host
        self.server_port = server_port

    def start(self) -> None:

        # connecting to server
        server = socket(AF_INET, SOCK_STREAM)
        server.connect((self.server_host, self.server_port))
        
        # bind socket to address 
        self.proxy.bind((self.host, self.port))
        self.proxy.listen(5)

        rlist = [server]
        messages_to_send = []

        print("Starting proxy on:", (self.host, self.port))

        while 1:
            # get readable and writeable socket 
            read_socks, write_socks, _ = select([self.proxy]+rlist, rlist, [])
            for read_sock in read_socks:
                try:
                    # if a new client tries to connect
                    if read_sock is self.proxy:
                        sock, addr = read_sock.accept()
                        print("\nNew connection from: ", (addr))
                        rlist.append(sock)
                        continue
                    data = read_sock.recv(1024)
                    if data:
                        if read_sock == server:
                            print(f"Server: <{data.decode('utf-8')}>")
                            # for now the proxy will broadcast the server's messages because there is only one server
                            for client in rlist:
                                if not client == server:
                                   client.send(data)
                        else:
                            # forward message to server
                            print(f"Client: <{data.decode('utf-8')}>")
                            server.send(data)
                    else:
                        print(1)
                        print(f"Closing connection with client")
                        rlist.remove(read_sock)
                        read_sock.close()
                    
                except Exception as error:
                    print(error)
                    print(f"Closing connection with client")
                    rlist.remove(read_sock)
                    read_sock.close()

            messages_to_send = self.send_waiting_messages(write_socks, messages_to_send)
    
    @staticmethod
    def handle(data) -> None:
        print(f"Client: <{data}>")
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
    # Create proxy object
    proxy = Proxy()

    
    # Start proxy
    proxy.start()

if __name__ == '__main__':
    main()
