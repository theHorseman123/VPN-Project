import socket as sock
from _thread import start_new_thread

def handler(s:sock):
    try:
        while 1:
            data = s.recv(1024)
            if data:
                print(f"\nProxy: <{data.decode('utf-8')}>")
            else:
                s.close()
                break
    except:
        s.close()


# Creating client socket
client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
# Connection to proxy
client.connect(("localhost", 8080))

print("Connected to proxy on: ", ("127.0.0.1", 8080))
start_new_thread(handler, (client, ))
try:
    while 1:
        msg = input("insert message: ")
        client.send(msg.encode("utf-8"))
except:
    pass
