$host = "192.168.1.100"; $port = 10050; $key = "system.uptime"; $tcp = New-Object Net.Sockets.TcpClient($host, $port); $stream = $tcp.GetStream(); $keyBytes = [System.Text.Encoding]::ASCII.GetBytes($key); $len = [BitConverter]::GetBytes([UInt64]$keyBytes.Length); $packet = ([System.Text.Encoding]::ASCII.GetBytes("ZBXD`x01") + $len + $keyBytes); $stream.Write($packet, 0, $packet.Length); $buffer = New-Object byte[] 4096; $bytesRead = $stream.Read($buffer, 0, $buffer.Length); if ($bytesRead -ge 13) { [System.Text.Encoding]::ASCII.GetString($buffer, 13, $bytesRead - 13) } else { "❌ Invalid response (too short: $bytesRead bytes)" }; $stream.Close(); $tcp.Close()


import socket
import struct

def zabbix_agent_get(host, port, key):
    header = b'ZBXD\x01'
    payload = key.encode('utf-8')
    length = struct.pack('<Q', len(payload))  # 8-byte little-endian
    request = header + length + payload

    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(request)
            # Receive header + length first
            response_header = sock.recv(13)
            if not response_header.startswith(b'ZBXD\x01'):
                print("❌ Invalid protocol header received from agent.")
                return
            data_length = struct.unpack('<Q', response_header[5:13])[0]
            # Receive full response payload
            response_body = b''
            while len(response_body) < data_length:
                chunk = sock.recv(data_length - len(response_body))
                if not chunk:
                    break
                response_body += chunk

            print(f"✔️ Response for key '{key}':\n{response_body.decode('utf-8')}")

    except Exception as e:
        print(f"❌ Error: {e}")

# Example usage
zabbix_agent_get("192.168.1.100", 10050, "system.uptime")
