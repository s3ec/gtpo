import socket
import struct

def zabbix_query(host, port, key):
    # Zabbix protocol header
    header = b'ZBXD\1'

    # Request body is just the key (e.g., system.uptime)
    data = key.encode()
    length = struct.pack('<Q', len(data))  # 8-byte little-endian

    packet = header + length + data

    try:
        with socket.create_connection((host, port), timeout=3) as sock:
            sock.sendall(packet)
            response = sock.recv(4096)
            if response.startswith(b'ZBXD\1'):
                length = struct.unpack('<Q', response[5:13])[0]
                payload = response[13:13+length].decode()
                print(f"✔️ Response for '{key}' from {host}:{port}:\n{payload}")
            else:
                print("❌ Invalid response from agent.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

# Example usage
zabbix_query("192.168.1.100", 10050, "system.uptime")
