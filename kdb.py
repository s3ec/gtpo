import pykx

ip = input("Enter IP (e.g. 127.0.0.1): ")
port = input("Enter Port (e.g. 5000): ")
cmd = input("Enter q command: ")

try:
    q = pykx.QConnection(host=ip, port=int(port))
    result = q(cmd)
    print("Result:", result)
except Exception as e:
    print("Error:", e)
