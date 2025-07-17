from qpython import qconnection

# Define host and port
host = '192.168.18.19'
port = 6212

# Create connection
q = qconnection.QConnection(host=host, port=port)

try:
    q.open()
    if q.is_connected():
        print(f"[+] Connected to KDB+ at {host}:{port}")

        # Send arithmetic query
        res1 = q.sendSync('2+2')
        print("[+] 2+2 =", res1)

        # Send system command
        res2 = q.sendSync('system "whoami"')
        print("[+] whoami output:", res2)
    else:
        print("[-] Failed to connect")

    q.close()

except Exception as e:
    print("[-] Error:", str(e))
