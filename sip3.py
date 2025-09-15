#!/usr/bin/env python3
"""
sip_probe_with_register.py
Enhanced SIP OPTIONS prober + optional REGISTER attempt (Digest auth handling).

Usage examples (lab only):
  # OPTIONS probing (default)
  python3 sip_probe_with_register.py targets.txt

  # OPTIONS probing + print raw responses only for NO_AUTH hits
  python3 sip_probe_with_register.py targets.txt --show-raw --only-noauth

  # Attempt REGISTER (TCP/TLS) with username/password (lab only)
  python3 sip_probe_with_register.py targets.txt --do-register --reg-user test --reg-pass secret --tls

IMPORTANT: Run only against systems you own or are authorized to test.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import ipaddress
import json
import os
import random
import socket
import ssl
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# -------------------------
# Templates / Helpers
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

OUTPUT_DIR_DEFAULT = "sip_probe_outputs"
_lock = threading.Lock()

def local_ip():
    """Guess an outbound local IP for headers (best-effort)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"

def make_options(ip, src_ip, port, transport, sport):
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

def parse_sip_response(text: str) -> dict:
    """
    Return dict: {status_line, status_code, headers (dict), body}
    Conservative parsing - tolerant to malformed responses.
    """
    out = {"status_line": "", "status_code": None, "headers": {}, "body": ""}
    if not text:
        return out
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines):
        first = lines[idx].strip()
        out["status_line"] = first
        parts = first.split()
        if len(parts) >= 2 and parts[0].upper().startswith("SIP/2.0"):
            try:
                out["status_code"] = int(parts[1])
            except Exception:
                out["status_code"] = None
    hdrs = {}
    i = idx + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            break
        if ":" in line:
            k, v = line.split(":", 1)
            hdrs[k.strip()] = v.strip()
        else:
            if hdrs:
                last = list(hdrs.keys())[-1]
                hdrs[last] = hdrs[last] + " " + line.strip()
        i += 1
    out["headers"] = hdrs
    out["body"] = "\n".join(lines[i:]) if i < len(lines) else ""
    return out

# -------------------------
# TCP/UDP recv helper
# -------------------------
def recv_all_tcp(sock: socket.socket, timeout: float, bufsize: int=8192) -> bytes:
    sock.settimeout(timeout)
    parts = []
    try:
        while True:
            chunk = sock.recv(bufsize)
            if not chunk:
                break
            parts.append(chunk)
            if b"SIP/2.0" in b"".join(parts) and len(b"".join(parts)) > 200:
                break
    except socket.timeout:
        pass
    except Exception:
        pass
    return b"".join(parts)

# -------------------------
# OPTIONS probes (TCP/UDP/TLS)
# -------------------------
def probe_tcp(ip, src_ip, port, timeout, use_tls=False):
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
        return {"target": ip, "result": "NO_RESPONSE", "reason": f"connect_err:{e}", "raw": "", "parsed": {}}
    try:
        if use_tls:
            try:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=ip)
            except Exception as e:
                sock.close()
                return {"target": ip, "result": "ERROR", "reason": f"tls_wrap_err:{e}", "raw": "", "parsed": {}}
        sock.sendall(payload)
    except Exception as e:
        try:
            sock.close()
        except Exception:
            pass
        return {"target": ip, "result": "ERROR", "reason": f"send_err:{e}", "raw": "", "parsed": {}}

    data = recv_all_tcp(sock, timeout)
    try:
        sock.close()
    except Exception:
        pass

    if not data:
        return {"target": ip, "result": "NO_RESPONSE", "reason": "", "raw": "", "parsed": {}}

    text = data.decode("utf-8", errors="ignore")
    parsed = parse_sip_response(text)
    first_line = parsed.get("status_line", "")

    if first_line.startswith("SIP/2.0 2") or ("SIP/2.0" in first_line and " 2" in first_line):
        result = "NO_AUTH"
    elif first_line and ("401" in first_line or "407" in first_line or parsed.get("status_code") in (401, 407)):
        result = "AUTH_REQUIRED"
    elif first_line:
        result = "OTHER_RESPONSE"
    else:
        result = "OTHER_RESPONSE"

    return {"target": ip, "result": result, "reason": first_line, "raw": text, "parsed": parsed}

def probe_udp(ip, src_ip, port, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sport = random.randint(20000, 50000)
    payload = make_options(ip, src_ip, port, "UDP", sport)
    try:
        sock.sendto(payload, (ip, port))
        try:
            data, addr = sock.recvfrom(8192)
        except socket.timeout:
            return {"target": ip, "result": "NO_RESPONSE", "reason": "", "raw": "", "parsed": {}}
        finally:
            sock.close()

        text = data.decode("utf-8", errors="ignore")
        parsed = parse_sip_response(text)
        first_line = parsed.get("status_line", "")

        if first_line.startswith("SIP/2.0 2") or ("SIP/2.0" in first_line and " 2" in first_line):
            result = "NO_AUTH"
        elif first_line and ("401" in first_line or "407" in first_line or parsed.get("status_code") in (401, 407)):
            result = "AUTH_REQUIRED"
        elif first_line:
            result = "OTHER_RESPONSE"
        else:
            result = "OTHER_RESPONSE"

        return {"target": ip, "result": result, "reason": first_line, "raw": text, "parsed": parsed}
    except Exception as e:
        return {"target": ip, "result": "ERROR", "reason": str(e), "raw": "", "parsed": {}}

# -------------------------
# REGISTER helpers (Digest handling)
# -------------------------
def parse_auth_header(header_value: str) -> dict:
    """
    Parse a WWW-Authenticate/Proxy-Authenticate header (Digest) into a dict.
    Example input: 'Digest realm="example", nonce="abc", qop="auth"'
    """
    out = {}
    if not header_value:
        return out
    h = header_value.strip()
    if h.lower().startswith("digest "):
        h = h[len("digest "):]
    # naive split on commas - adequate for common fields
    parts = []
    cur = ""
    in_quote = False
    for ch in h:
        if ch == '"' and not in_quote:
            in_quote = True
            cur += ch
        elif ch == '"' and in_quote:
            in_quote = False
            cur += ch
        elif ch == ',' and not in_quote:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"')
            out[k] = v
    return out

def make_digest_auth(username: str, password: str, method: str, uri: str, auth_params: dict, nc_int: int = 1, cnonce: str = None) -> str:
    """
    Compute Digest authorization header value (supports MD5, qop=auth).
    Returns 'Digest ...' string.
    """
    realm = auth_params.get("realm", "")
    nonce = auth_params.get("nonce", "")
    qop = auth_params.get("qop", "")
    algorithm = (auth_params.get("algorithm") or "MD5").lower()

    if algorithm != "md5":
        raise ValueError("Unsupported algorithm: " + str(algorithm))

    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()

    qop_used = None
    if qop:
        qop_list = [x.strip() for x in qop.split(",")]
        if "auth" in qop_list:
            qop_used = "auth"
        else:
            qop_used = qop_list[0]

    if qop_used:
        if cnonce is None:
            cnonce = hashlib.md5((str(time.time()) + str(random.random())).encode()).hexdigest()[:16]
        nc_value = f"{nc_int:08x}"
        resp = hashlib.md5(f"{ha1}:{nonce}:{nc_value}:{cnonce}:{qop_used}:{ha2}".encode()).hexdigest()
    else:
        cnonce = None
        nc_value = None
        resp = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

    auth_parts = [
        f'username="{username}"',
        f'realm="{realm}"',
        f'nonce="{nonce}"',
        f'uri="{uri}"',
        f'response="{resp}"'
    ]
    if auth_params.get("opaque"):
        auth_parts.append(f'opaque="{auth_params.get("opaque")}"')
    if qop_used:
        auth_parts.append(f'qop={qop_used}')
        auth_parts.append(f'nc={nc_value}')
        auth_parts.append(f'cnonce="{cnonce}"')
    if algorithm:
        auth_parts.append(f'algorithm={algorithm.upper()}')

    return "Digest " + ", ".join(auth_parts)

def probe_register(ip, src_ip, port, timeout, username, password, use_tls=False, transport="TCP"):
    """
    Attempt SIP REGISTER. Returns dict:
      { target, result, reason, raw, parsed }
    Possible result values:
      REGISTER_SUCCESS, REGISTER_AUTH_REQUIRED, REGISTER_REJECTED, REGISTER_ERROR, NO_RESPONSE
    NOTE: Uses TCP/TLS only (REGISTER over UDP is possible but less common).
    """
    # Build first REGISTER (CSeq 1)
    sport = random.randint(20000, 50000)
    branch = "z9hG4bK" + str(random.randint(1000000, 9999999))
    callid = str(random.randint(100000, 999999))
    from_tag = str(random.randint(10000, 99999))
    uri = f"sip:{ip}:{port}"
    contact = f"<sip:{username}@{src_ip}:{sport}>"
    register_template = (
        "REGISTER {uri} SIP/2.0\r\n"
        "Via: SIP/2.0/{transport} {src_ip}:{sport};branch={branch}\r\n"
        "Max-Forwards: 70\r\n"
        "From: \"{username}\" <sip:{username}@{ip}>;tag={from_tag}\r\n"
        "To: \"{username}\" <sip:{username}@{ip}>\r\n"
        "Call-ID: {callid}@{src_ip}\r\n"
        "CSeq: 1 REGISTER\r\n"
        "Contact: {contact}\r\n"
        "Expires: 3600\r\n"
        "User-Agent: SIPProbe/1.0\r\n"
        "Content-Length: 0\r\n\r\n"
    )
    payload1 = register_template.format(
        uri=uri, transport=transport, src_ip=src_ip, sport=sport, branch=branch,
        username=username, ip=ip, from_tag=from_tag, callid=callid, contact=contact
    ).encode("utf-8")

    # send first REGISTER
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
    except Exception as e:
        try: sock.close()
        except Exception: pass
        return {"target": ip, "result": "NO_RESPONSE", "reason": f"connect_err:{e}", "raw": "", "parsed": {}}
    try:
        if use_tls:
            try:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=ip)
            except Exception as e:
                sock.close()
                return {"target": ip, "result": "ERROR", "reason": f"tls_wrap_err:{e}", "raw": "", "parsed": {}}
        sock.sendall(payload1)
    except Exception as e:
        try: sock.close()
        except Exception: pass
        return {"target": ip, "result": "ERROR", "reason": f"send_err:{e}", "raw": "", "parsed": {}}

    data = recv_all_tcp(sock, timeout)
    try: sock.close()
    except Exception: pass

    if not data:
        return {"target": ip, "result": "NO_RESPONSE", "reason": "", "raw": "", "parsed": {}}

    text = data.decode("utf-8", errors="ignore")
    parsed = parse_sip_response(text)
    first_line = parsed.get("status_line", "")

    # If 401/407, parse challenge and retry
    if (first_line and ("401" in first_line or "407" in first_line)) or parsed.get("status_code") in (401, 407):
        headers = parsed.get("headers", {})
        auth_hdr = headers.get("WWW-Authenticate") or headers.get("Proxy-Authenticate") or ""
        auth_params = parse_auth_header(auth_hdr)
        try:
            auth_header = make_digest_auth(username, password, "REGISTER", uri, auth_params, nc_int=1)
        except Exception as e:
            return {"target": ip, "result": "REGISTER_ERROR", "reason": f"digest_err:{e}", "raw": text, "parsed": parsed}

        # build second REGISTER (CSeq 2) with Authorization
        sport2 = random.randint(20000, 50000)
        branch2 = "z9hG4bK" + str(random.randint(1000000, 9999999))
        callid2 = str(random.randint(100000, 999999))
        from_tag2 = str(random.randint(10000, 99999))
        contact2 = f"<sip:{username}@{src_ip}:{sport2}>"
        register_template2 = (
            "REGISTER {uri} SIP/2.0\r\n"
            "Via: SIP/2.0/{transport} {src_ip}:{sport};branch={branch}\r\n"
            "Max-Forwards: 70\r\n"
            "From: \"{username}\" <sip:{username}@{ip}>;tag={from_tag}\r\n"
            "To: \"{username}\" <sip:{username}@{ip}>\r\n"
            "Call-ID: {callid}@{src_ip}\r\n"
            "CSeq: 2 REGISTER\r\n"
            "Contact: {contact}\r\n"
            "Authorization: {auth}\r\n"
            "Expires: 3600\r\n"
            "User-Agent: SIPProbe/1.0\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        payload2 = register_template2.format(
            uri=uri, transport=transport, src_ip=src_ip, sport=sport2, branch=branch2,
            username=username, ip=ip, from_tag=from_tag2, callid=callid2, contact=contact2, auth=auth_header
        ).encode("utf-8")

        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.settimeout(timeout)
        try:
            sock2.connect((ip, port))
        except Exception as e:
            try: sock2.close()
            except Exception: pass
            return {"target": ip, "result": "REGISTER_ERROR", "reason": f"connect_err2:{e}", "raw": text, "parsed": parsed}
        try:
            if use_tls:
                try:
                    context = ssl.create_default_context()
                    sock2 = context.wrap_socket(sock2, server_hostname=ip)
                except Exception as e:
                    sock2.close()
                    return {"target": ip, "result": "ERROR", "reason": f"tls_wrap_err2:{e}", "raw": text, "parsed": parsed}
            sock2.sendall(payload2)
        except Exception as e:
            try: sock2.close()
            except Exception: pass
            return {"target": ip, "result": "REGISTER_ERROR", "reason": f"send_err2:{e}", "raw": text, "parsed": parsed}

        data2 = recv_all_tcp(sock2, timeout)
        try: sock2.close()
        except Exception: pass

        text2 = data2.decode("utf-8", errors="ignore") if data2 else ""
        parsed2 = parse_sip_response(text2)
        first2 = parsed2.get("status_line", "")

        combined_raw = text + "\n\n---> RETRY WITH AUTH --->\n\n" + text2

        if first2.startswith("SIP/2.0 2") or ("SIP/2.0" in first2 and " 2" in first2):
            return {"target": ip, "result": "REGISTER_SUCCESS", "reason": first2, "raw": combined_raw, "parsed": parsed2}
        else:
            if first2 and ("401" in first2 or "407" in first2 or parsed2.get("status_code") in (401,407)):
                return {"target": ip, "result": "REGISTER_AUTH_REQUIRED", "reason": first2, "raw": combined_raw, "parsed": parsed2}
            else:
                return {"target": ip, "result": "REGISTER_REJECTED", "reason": first2 or "no_resp", "raw": combined_raw, "parsed": parsed2}
    else:
        # No challenge: treat 2xx as success, others as rejected
        if first_line.startswith("SIP/2.0 2") or ("SIP/2.0" in first_line and " 2" in first_line):
            return {"target": ip, "result": "REGISTER_SUCCESS", "reason": first_line, "raw": text, "parsed": parsed}
        else:
            return {"target": ip, "result": "REGISTER_REJECTED", "reason": first_line or "no_resp", "raw": text, "parsed": parsed}

# -------------------------
# Input loader (file, CSV, CIDR)
# -------------------------
def load_ips_from_arg(arg: str) -> list:
    """Accepts filename, single IP/hostname, comma-separated list, or CIDR."""
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as fh:
            entries = [line.strip() for line in fh if line.strip() and not line.strip().startswith("#")]
    else:
        entries = [part.strip() for part in arg.split(",") if part.strip()]

    ips = []
    for e in entries:
        try:
            if "/" in e:
                net = ipaddress.ip_network(e, strict=False)
                for a in net.hosts():
                    ips.append(str(a))
                continue
        except Exception:
            pass
        ips.append(e)
    return ips

# -------------------------
# Reporting helpers
# -------------------------
def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)

def pretty_print_table(rows, columns):
    widths = [len(col) for col in columns]
    for r in rows:
        for i, col in enumerate(columns):
            widths[i] = max(widths[i], len(str(r.get(col, ""))))
    sep = " | "
    hdr = sep.join(col.ljust(widths[i]) for i, col in enumerate(columns))
    line = "-+-".join("-" * widths[i] for i in range(len(columns)))
    print(hdr)
    print(line)
    for r in rows:
        print(sep.join(str(r.get(col, "")).ljust(widths[i]) for i, col in enumerate(columns)))

def pretty_print_raw(ip, raw, meta):
    print("\n" + "="*80)
    print(f"RAW SIP RESPONSE: {ip}")
    print(f"Result: {meta.get('result')}  Reason: {meta.get('reason')}")
    headers = meta.get("parsed", {}).get("headers", {}) if meta.get("parsed") else {}
    if headers:
        print("Summary headers:")
        for k in ("Server", "User-Agent", "Allow", "WWW-Authenticate", "Proxy-Authenticate", "Contact"):
            if headers.get(k):
                print(f"  {k}: {headers.get(k)}")
    print("-"*80)
    if raw:
        maxlen = 50000
        if len(raw) > maxlen:
            print(raw[:maxlen])
            print(f"... (truncated, total {len(raw)} bytes) ...")
        else:
            print(raw)
    else:
        print("(no raw response available)")
    print("="*80 + "\n")

# -------------------------
# CLI and main
# -------------------------
def parse_args():
    p = argparse.ArgumentParser(description="SIP OPTIONS probe + optional REGISTER (Digest) with neat output")
    p.add_argument("targets", help="file with IPs/CIDRs, single IP/hostname, or comma-separated list")
    p.add_argument("--proto", choices=["tcp", "udp"], default="tcp", help="transport (tcp or udp), default tcp")
    p.add_argument("--port", type=int, default=None, help="port to probe (default 5061 for TLS, else 5060)")
    p.add_argument("--timeout", type=float, default=3.0, help="connect/recv timeout in seconds")
    p.add_argument("--workers", type=int, default=40, help="concurrency / thread workers")
    p.add_argument("--outdir", default=OUTPUT_DIR_DEFAULT, help="output directory")
    p.add_argument("--csv", default="results.csv", help="CSV filename (in outdir)")
    p.add_argument("--json", default="results.json", help="JSON filename (in outdir)")
    p.add_argument("--tls", action="store_true", help="use TLS (wrap TCP socket) - default port becomes 5061 if --port not set")
    p.add_argument("--show-raw", "-R", action="store_true", help="print raw SIP response(s) to console")
    p.add_argument("--only-noauth", action="store_true", help="when used with --show-raw, only print raw when result == NO_AUTH")
    # Register-specific
    p.add_argument("--do-register", action="store_true", help="attempt SIP REGISTER flow (lab only)")
    p.add_argument("--reg-user", default="test", help="username for REGISTER")
    p.add_argument("--reg-pass", default="", help="password for REGISTER (empty attempts anonymous/no-pass)")
    return p.parse_args()

def main():
    args = parse_args()
    portsuggest = 5061 if args.tls else 5060
    port = args.port if args.port is not None else portsuggest

    ips = load_ips_from_arg(args.targets)
    if not ips:
        print("No targets found. Exiting.", file=sys.stderr)
        sys.exit(2)

    src = local_ip()
    print(f"# scanner_src_ip: {src}")
    print(f"# probes: {len(ips)}, proto: {args.proto}, port: {port}, timeout: {args.timeout}, tls: {args.tls}, do_register: {args.do_register}")

    ensure_dir(args.outdir)
    raw_dir = os.path.join(args.outdir, "raw_responses")
    ensure_dir(raw_dir)

    if args.do_register:
        # REGISTER uses TCP/TLS; ensure proto is tcp for clarity
        probe_fn = (lambda ip: probe_register(ip, src, port, args.timeout, args.reg_user, args.reg_pass, use_tls=args.tls, transport="TCP"))
    else:
        probe_fn = (lambda ip: probe_tcp(ip, src, port, args.timeout, use_tls=args.tls)) if args.proto == "tcp" else (lambda ip: probe_udp(ip, src, port, args.timeout))

    results = []
    counter = Counter()
    failures = []

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(probe_fn, ip): ip for ip in ips}
        for fut in as_completed(futures):
            ip = futures[fut]
            try:
                res = fut.result()
            except Exception as e:
                res = {"target": ip, "result": "ERROR", "reason": str(e), "raw": "", "parsed": {}}

            target = res.get("target", ip)
            result = res.get("result", "ERROR")
            reason = (res.get("reason") or "").replace("\n", " ").replace(",", ";")[:400]
            raw = res.get("raw", "")
            parsed = res.get("parsed", {})

            headers = parsed.get("headers", {}) if parsed else {}
            server = headers.get("Server") or headers.get("User-Agent") or ""
            allow = headers.get("Allow", "")
            www = headers.get("WWW-Authenticate", headers.get("Proxy-Authenticate", ""))

            row = {
                "ip": target,
                "result": result,
                "reason": reason,
                "server": server,
                "allow": allow,
                "www_auth": www
            }

            results.append({"meta": row, "raw": raw, "parsed": parsed})
            counter[result] += 1
            if result in ("ERROR", "NO_RESPONSE"):
                failures.append(target)

            # save raw to file for later analysis
            try:
                safe_name = target.replace(":", "_")
                fname = os.path.join(raw_dir, f"{safe_name}.txt")
                with open(fname, "w", encoding="utf-8") as fh:
                    fh.write(f"# probe: {datetime.utcnow().isoformat()}Z\n")
                    fh.write(f"# proto: {args.proto}, port: {port}, tls: {args.tls}, do_register: {args.do_register}\n\n")
                    if raw:
                        fh.write(raw)
                    else:
                        fh.write(f"(no raw response) reason={reason}\n")
            except Exception:
                pass

            # optionally print raw to console
            if args.show_raw:
                if not args.only_noauth or (args.only_noauth and result == "NO_AUTH"):
                    meta_for_print = {"result": result, "reason": reason, "parsed": parsed}
                    pretty_print_raw(target, raw, meta_for_print)

    # Prepare CSV rows and JSON output
    csv_rows = []
    json_out = {"generated_at": datetime.utcnow().isoformat() + "Z", "summary": {}, "results": []}
    for item in results:
        m = item["meta"]
        csv_rows.append({
            "ip": m["ip"],
            "result": m["result"],
            "reason": m["reason"],
            "server": m["server"],
            "allow": m["allow"],
            "www_auth": m["www_auth"]
        })
        json_out["results"].append({
            "ip": m["ip"],
            "result": m["result"],
            "reason": m["reason"],
            "server": m["server"],
            "allow": m["allow"],
            "www_auth": m["www_auth"],
            "parsed": item.get("parsed", {}),
            "raw_filename": os.path.join("raw_responses", f"{m['ip'].replace(':', '_')}.txt")
        })

    json_out["summary"] = {"total": len(results), **dict(counter)}

    # write outputs
    try:
        write_csv(os.path.join(args.outdir, args.csv), csv_rows, fieldnames=["ip","result","reason","server","allow","www_auth"])
        write_json(os.path.join(args.outdir, args.json), json_out)
    except Exception as e:
        print(f"Failed to write outputs: {e}", file=sys.stderr)

    # pretty terminal table (top results)
    table_rows = []
    for r in csv_rows:
        table_rows.append({
            "IP": r["ip"],
            "RESULT": r["result"],
            "SERVER": (r["server"][:30] + "...") if r["server"] and len(r["server"])>30 else r["server"],
            "WWW_AUTH": ("yes" if r["www_auth"] else ""),
            "REASON": (r["reason"][:40] + "...") if r["reason"] and len(r["reason"])>43 else r["reason"]
        })

    print("\nSummary:")
    print(f"  Total scanned: {json_out['summary']['total']}")
    for k, v in counter.items():
        print(f"  {k}: {v}")
    print(f"\nRaw responses saved to: {os.path.abspath(raw_dir)}")
    print(f"CSV: {os.path.abspath(os.path.join(args.outdir, args.csv))}")
    print(f"JSON: {os.path.abspath(os.path.join(args.outdir, args.json))}\n")

    preview = table_rows[:200]
    if preview:
        pretty_print_table(preview, ["IP","RESULT","SERVER","WWW_AUTH","REASON"])
    else:
        print("(no results)")

    if failures:
        print("\nFailures / no-responses (sample up to 20):")
        for f in failures[:20]:
            print("  -", f)

if __name__ == "__main__":
    main()
