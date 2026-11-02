import os
import socket
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(5)

print("=" * 45)
print("TCP SERVER STARTED")
print(f"Host: {HOST}")
print(f"Port: {PORT}")
print("Waiting for connections...")
print("=" * 45)

try:
    while True:
        conn, addr = server.accept()

        print(f"\n[CONNECTED] {addr[0]}:{addr[1]}")

        buffer = b""

        try:
            while True:
                data = conn.recv(4096)

                if not data:
                    break

                buffer += data

                while b"\n" in buffer:
                    message, buffer = buffer.split(b"\n", 1)
                    message = message.decode("utf-8").strip()

                    if not message:
                        continue

                    print(f"[RECEIVED] {message}")

                    response = message.upper()

                    conn.sendall((response + "\n").encode("utf-8"))

                    print(f"[SENT] {response}")

        except ConnectionError:
            print("[ERROR] Connection lost")

        finally:
            conn.close()
            print(f"[DISCONNECTED] {addr[0]}:{addr[1]}")

except KeyboardInterrupt:
    print("\n[SERVER] Shutting down...")

finally:
    server.close()