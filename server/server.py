import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("0.0.0.0", 5000))
server.listen(1)

print("Server is running...")
print("Waiting for client...")

conn, addr = server.accept()
print(f"Client connected: {addr}")

while True:
    data = conn.recv(1024)

    if not data:
        break

    message = data.decode("utf-8")
    print(f"Received: {message}")

    response = message.upper()
    conn.sendall(response.encode("utf-8"))

    print(f"Sent: {response}")

conn.close()
server.close()
