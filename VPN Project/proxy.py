import socket as sock
import scapy.all
from select import select
from _thread import start_new_thread


class Proxy:

    def __init__(self, host="127.0.0.1", port=8080) -> None:
        self.host = host
        self.port = port


    def https_request(self, client_sock, addr, request):
        
        web_host, web_port = request.split(b" ")[1].split(b":")
        request_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        
        try:
            request_sock.connect((web_host.decode('utf-8'), int(web_port)))
            print("connected succesfully to", (web_host, int(web_port)))

        except Exception as error:
            print("Couldn't Connect web server at:", (web_host, web_port))
            client_sock.send(str(error).encode("utf-8"))
            client_sock.close()
        
        reply = "HTTP/1.0 200 Connection established\r\nProxy-agent: HorseMan_Tunnel\r\n\r\n"
        client_sock.send(reply.encode())

        request_sock.setblocking(False)
        client_sock.setblocking(False)

        # transfer messages back and forth
        while 1:
            try:
                data = client_sock.recv(4098)
                request.sendall(data)
            except BlockingIOError as error:
                pass
            except Exception as error:
                break

            try:
                data = request.recv(4098)
                client_sock.sendall(data)
            except BlockingIOError as error:
                pass
            except Exception as error:
                break 
    
    def http_request(self, client_sock, addr, request):
        # initializing socket to webserver
        host_line = [data for data in request.split(b"\r\n") if b"Host:" in data][0]
        print(host_line)

        if len(host_line) < 1:
            client_sock.close()
            return
        
        web_server_data = host_line.split(b":")[1:]
        web_server, port = web_server_data[0].strip(), 80 if len(web_server_data) == 1 else web_server_data[1]

        request_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

        try:
            request_sock.connect((web_server.decode(), int(port)))
        except Exception as error:
            print("Failed to connect to:", (web_server.decode(), int(port)))
            client_sock.close()
            print(error)
            return
        
        reply = request[:request.find(b" ") + 1] + request[request.find(b"/",request.find(b"//") + 2):]
        try:
            request_sock.sendall(reply)
        except:
            client_sock.close()
            request_sock.close()
            return

        data = b''
        data_fragment = b'1'

        while data_fragment:
            try:
                data_fragment = request_sock.recv(4096)
            except:
                break

            data = data + data_fragment
        else:
            try:
                client_sock.sendall(data)
            except:
                client_sock.close()
                request_sock.close()

        request_sock.close()
        client_sock.close()


    def client_handler(self, client_sock, addr):
        
        try:
            request = client_sock.recv(4098)
            if request:
                http_method = request.split(b" ")[0]
                if http_method == b"CONNECT":
                    self.https_request(client_sock, addr, request)
                else:
                    self.http_request(client_sock, addr, request)
            else:
                client_sock.close()
        except Exception as error:
            raise error

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
    proxy = Proxy(host="10.100.102.93")

    # Start proxy
    proxy.notify_server(server_ip="10.100.102.93")
    proxy.mainloop()
    
if __name__ == '__main__':
    main()
