

import argparse
import os
import random
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------
# Helpers / Templates
# -------------------------
SIP_OPTIONS_TEMPLATE = (
    "OPTIONS sip:{ip}:{port} SIP/2.0\r\n"
    "Via: SIP/2.0/{transport} {src_ip}:{sport};branch={branch}\r\n"
    "Max-Forwards: 70\r\n"
    "From: <sip:scanner@{src_ip}>;tag={from_tag}\r\n"
    "To: <sip:target@{ip}>\r\n"
    "Call-ID: {callid}@{src_ip}\r\n"
    "CSeq: 1 OPTIONS\r\n"
    "Contact: <sip:scanner@{src_ip}:{sport}>\r\n"
    "User-Agent: SIPProbe/1.0\r\n"
    "Content-Length: 0\r\n\r\n"
)

def local_ip():
    """Try to guess an outbound local IP for use in headers (best-effort)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # no actual connection performed
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"

def make_options(ip, src_ip, port, transport, sport):
    """Return bytes SIP OPTIONS payload (port included in SIP URI)."""
    return SIP_OPTIONS_TEMPLATE.format(
        ip=ip,
        port=port,
        transport=transport.upper(),
        src_ip=src_ip,
        sport=sport,
        branch="z9hG4bK" + str(random.randint(1000000, 9999999)),
        from_tag=str(random.randint(10000, 99999)),
        callid=str(random.randint(100000, 999999))
    ).encode("utf-8")

# -------------------------
# Probing functions
# -------------------------
def probe_udp(ip, src_ip, port, timeout):
    """Send UDP OPTIONS -> return tuple (ip, result, reason)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sport = random.randint(20000, 50000)  # random source port for header
    payload = make_options(ip, src_ip, port, "UDP", sport)
    try:
        # send from an ephemeral port (OS picks) but include sport in headers for clarity
        sock.sendto(payload, (ip, port))
        try:
            data, addr = sock.recvfrom(8192)
        except socket.timeout:
            return ip, "NO_RESPONSE", ""
        finally:
            sock.close()

        text = data.decode("utf-8", errors="ignore")
        first_line = text.splitlines()[0].strip() if text else ""

        # classify
        if first_line.startswith("SIP/2.0 2") or ("SIP/2.0" in first_line and " 2" in first_line):
            return ip, "NO_AUTH", first_line
        if "401" in first_line or "407" in first_line:
            return ip, "AUTH_REQUIRED", first_line
        if first_line:
            return ip, "OTHER_RESPONSE", first_line
        return ip, "OTHER_RESPONSE", text[:120].replace("\n", " ")
    except Exception as e:
        return ip, "ERROR", str(e)

def recv_all_tcp(sock, timeout, bufsize=8192):
    """Read until socket times out or remote closes (best-effort)."""
    sock.settimeout(timeout)
    parts = []
    try:
        while True:
            chunk = sock.recv(bufsize)
            if not chunk:
                break
            parts.append(chunk)
            # small heuristic: stop if we have a SIP status line and some body
            if b"SIP/2.0" in b"".join(parts) and len(b"".join(parts)) > 200:
                break
    except socket.timeout:
        pass
    except Exception:
        pass
    return b"".join(parts)

def probe_tcp(ip, src_ip, port, timeout):
    """Connect TCP -> send OPTIONS -> receive -> classify."""
    sport = random.randint(20000, 50000)
    payload = make_options(ip, src_ip, port, "TCP", sport)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
    except Exception as e:
        try:
            sock.close()
        except Exception:
            pass
        return ip, "NO_RESPONSE", f"connect_err:{e}"

    try:
        sock.sendall(payload)
    except Exception as e:
        sock.close()
        return ip, "ERROR", f"send_err:{e}"

    data = recv_all_tcp(sock, timeout)
    try:
        sock.close()
    except Exception:
        pass

    if not data:
        return ip, "NO_RESPONSE", ""

    text = data.decode("utf-8", errors="ignore")
    first_line = text.splitlines()[0].strip() if text else ""

    if first_line.startswith("SIP/2.0 2") or ("SIP/2.0" in first_line and " 2" in first_line):
        return ip, "NO_AUTH", first_line
    if "401" in first_line or "407" in first_line:
        return ip, "AUTH_REQUIRED", first_line
    if first_line:
        return ip, "OTHER_RESPONSE", first_line
    return ip, "OTHER_RESPONSE", text[:200].replace("\n", " ")

# -------------------------
# Input loader
# -------------------------
def load_ips_from_arg(arg):
    """Accepts filename, single IP/hostname, or comma-separated list."""
    if os.path.isfile(arg):
        with open(arg, "r") as fh:
            return [line.strip() for line in fh if line.strip() and not line.strip().startswith("#")]
    if "," in arg:
        return [part.strip() for part in arg.split(",") if part.strip()]
    # treat as single
    return [arg.strip()]

# -------------------------
# Main
# -------------------------
def parse_args():
    p = argparse.ArgumentParser(description="SIP OPTIONS probe (TCP/UDP) for auth detection")
    p.add_argument("targets", help="file with IPs, single IP, or comma-separated list")
    p.add_argument("--proto", choices=["tcp", "udp"], default="tcp", help="transport (tcp or udp), default tcp")
    p.add_argument("--port", type=int, default=5060, help="port to probe (default 5060)")
    p.add_argument("--timeout", type=float, default=3.0, help="connect/recv timeout in seconds")
    p.add_argument("--workers", type=int, default=40, help="concurrency / thread workers")
    return p.parse_args()

def main():
    args = parse_args()
    ips = load_ips_from_arg(args.targets)
    if not ips:
        print("No targets found. Exiting.", file=sys.stderr)
        sys.exit(2)

    src = local_ip()
    print(f"# scanner_src_ip: {src}")
    print("ip,result,reason")

    probe_fn = probe_tcp if args.proto == "tcp" else probe_udp

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(probe_fn, ip, src, args.port, args.timeout): ip for ip in ips}
        for fut in as_completed(futures):
            ip = futures[fut]
            try:
                ip, result, reason = fut.result()
            except Exception as e:
                ip, result, reason = ip, "ERROR", str(e)
            safe_reason = reason.replace(",", ";").replace("\n", " ").strip()
            print(f"{ip},{result},{safe_reason}")

if __name__ == "__main__":
    main()
