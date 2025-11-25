import socket
import sys

TARGET = "192.168.1.1"

# Read port dynamically
if len(sys.argv) < 2:
    print("Usage: python giop_probe.py <PORT>")
    sys.exit(1)

try:
    PORT = int(sys.argv[1])
except ValueError:
    print("Port must be an integer.")
    sys.exit(1)

OBJECT_KEYS = [
    b"NameService",
    b"RootPOA",
    b"Manager",
    b"Admin",
    b"System",
    b"Console",
    b"ORBProxy",
    b"Service",
    b"Server",
    b"Default",
    b"",  # empty key
]

def send_locate_request(key):
    req_id = 0x12345678
    key_len = len(key)
    header = b"GIOP\x01\x00\x00\x05" + (8 + key_len).to_bytes(4, 'big')
    body = req_id.to_bytes(4, 'big') + key_len.to_bytes(4, 'big') + key
    return header + body

def parse_locate_reply(data):
    if len(data) < 20:
        return "TOO SHORT"
    msg_type = data[7]
    if msg_type != 0x06:
        return f"NOT_LOCATE_REPLY ({hex(msg_type)})"
    status = data[-1]
    statuses = {
        0: "OBJECT_HERE",
        1: "OBJECT_FORWARD",
        2: "UNKNOWN_OBJECT",
        3: "LOC_SYSTEM_EXCEPTION"
    }
    return statuses.get(status, f"UNKNOWN_STATUS({status})")

def test_key(key):
    try:
        with socket.create_connection((TARGET, PORT), timeout=3) as s:
            s.send(send_locate_request(key))
            resp = s.recv(256)
            result = parse_locate_reply(resp)
            print(f"[{result:20}] {key.decode() if key else '(empty)'}")
    except Exception as e:
        print(f"[{'ERROR':20}] {key.decode() if key else '(empty)'} → {str(e)}")

if __name__ == "__main__":
    print(f"Probing GIOP service at {TARGET}:{PORT}")
    print("-" * 50)
    for key in OBJECT_KEYS:
        test_key(key)
