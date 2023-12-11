import socket as sock

# Creating client socket
client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
# Connection to proxy
client.connect(("localhost", 8080))

while 1:
    msg = input("insert message: ")
    client.send(msg.encode("utf-8"))
    data = client.recv(1024)
    print(data)
    if data:
        print(f"Proxy: <{data.decode('utf-8')}>")
    else:
        client.close()
        break
