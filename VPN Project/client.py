import socket as sock
import winreg
import sys
from _thread import start_new_thread


root = winreg.HKEY_CURRENT_USER
reg_key = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


class Client:
    def __init__(self, host = "localhost", port = 0):

        self.host = host
        self.port = port

        self.proxies = []

    def connect_proxy(self):

        while 1:
            if len(self.proxies) < 1:
                print("No active proxies")
                return

            proxy = self.proxies[0]
            try:
                client_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
                client_sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
                client_sock.settimeout(5)

                print(proxy)
                client_sock.connect((proxy))
                print("Connected to proxy succesfully at: ", (proxy))
                break

            except TimeoutError:
                self.proxies.remove(proxy)
                client_sock.close()
                continue

        
        client_sock.settimeout(None)
        
        proxy_server = ":".join((proxy[0], str(proxy[1])))

        try:
            with winreg.OpenKey(root, reg_key, 0, winreg.KEY_ALL_ACCESS) as key:
                # Set proxy enabled
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)

                # Set proxy server address
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)

                while 1:
                    print(client_sock.recv(4096))

        except FileNotFoundError:
            print("Registry key not found.")

        except PermissionError:
            print("Insufficient permissions to modify registry.")

    def get_proxies(self, server_ip = "localhost", server_port = 1234):
        client_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        client_sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)

        try:
            client_sock.bind((server_ip, 0))
            client_sock.connect((server_ip, server_port))
            print("connection established with server at:", (server_ip, server_port))
            
            client_sock.send("get".encode('utf-8'))
            data = client_sock.recv(1024)
            if data:
                data = data.decode('utf-8')
                data = data.split("/")
                for i in range(1, len(data), 2):
                    try:
                        self.proxies.append((data[i], int(data[i+1])))
                    except Exception:
                        continue
            else:
                print("The server is offline")
                client_sock.close()

        except Exception as error:
            client_sock.close()
            raise error
        

def main():
    # Create server object
    client = Client(host="10.100.102.93")

    # Start server
    client.get_proxies(server_ip="10.100.102.93")
    print(client.proxies)
    client.connect_proxy()

if __name__ == '__main__':
    main()
