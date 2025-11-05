#!/usr/bin/env python3
# quake1_connect.py — test TCP connection to Quake1 server (port 26000)
# Usage: python quake1_connect.py <ip> [port]

import socket, sys, struct

ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 26000

try:
    s = socket.create_connection((ip, port), timeout=3)
    print(f"Connected to Quake1 server at {ip}:{port}")

    # Quake1 TCP protocol messages are framed with a 4-byte length header.
    # The first client message normally is a "connect" command string.
    # Example: "\x01connect 26000 3 0 \"playername\" 0\n"
    msg = b"\x01connect 26000 3 0 \"python_client\" 0\n"
    packet = struct.pack("<l", len(msg)) + msg
    s.sendall(packet)

    # Receive first bytes of the server's reply (usually begins with 4-byte length + code)
    data = s.recv(1024)
    print("Raw reply:", data)

except Exception as e:
    print("Connection failed:", e)
finally:
    s.close()
