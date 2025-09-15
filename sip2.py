#!/usr/bin/env python3
"""
sip_probe_report.py
Enhanced SIP OPTIONS prober with neat outputs and raw-response printing.

Usage examples:
  python3 sip_probe_report.py targets.txt --proto tcp --port 5060 --workers 100
  python3 sip_probe_report.py 192.168.1.0/28 --proto udp --port 5060
  python3 sip_probe_report.py 1.2.3.4 --proto tcp --tls --port 5061 --show-raw --only-noauth

IMPORTANT: Use only on systems you own or have explicit permission to test.
"""
import argparse
import csv
import ipaddress
import json
import os
import random
import socket
import ssl
import sys
import threading
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

def parse_sip_response(text):
    """
    Return dict: {status_line, status_code, headers (dict), body}
    Conservative parsing - tolerant to malformed responses.
    """
    out = {"status_line": "", "status_code": None, "headers": {}, "body": ""}
    if not text:
        return out
    lines = text.splitlines()
    # find first non-empty line
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
        if not line.strip():  # blank => end of headers
            i += 1
            break
        if ":" in line:
            k, v = line.split(":", 1)
            hdrs[k.strip()] = v.strip()
        else:
            # continuation or malformed — attach to last header if present
            if hdrs:
                last = list(hdrs.keys())[-1]
                hdrs[last] = hdrs[last] + " " + line.strip()
        i += 1
    out["headers"] = hdrs
    out["body"] = "\n".join(lines[i:]) if i < len(lines) else ""
    return out

# -------------------------
# Probing (TCP/UDP/TLS)
# -------------------------
def recv_all_tcp(sock, timeout, bufsize=8192):
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
# Input loader (files, comma lists, CIDR)
# -------------------------
def load_ips_from_arg(arg):
    """Accepts filename, single IP/hostname, comma-separated list, or CIDR."""
    if os.path.isfile(arg):
        with open(arg, "r") as fh:
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
    """Print a clearly delimited raw SIP response to stdout."""
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
# Main
# -------------------------
def parse_args():
    p = argparse.ArgumentParser(description="SIP OPTIONS probe (TCP/UDP/TLS) with neat output")
    p.add_argument("targets", help="file with IPs/CIDRs, single IP/hostname, or comma-separated list")
    p.add_argument("--proto", choices=["tcp", "udp"], default="tcp", help="transport (tcp or udp), default tcp")
    p.add_argument("--port", type=int, default=None, help="port to probe (default 5061 for TLS, else 5060)")
    p.add_argument("--timeout", type=float, default=3.0, help="connect/recv timeout in seconds")
    p.add_argument("--workers", type=int, default=40, help="concurrency / thread workers")
    p.add_argument("--outdir", default=OUTPUT_DIR_DEFAULT, help="output directory")
    p.add_argument("--csv", default="results.csv", help="CSV filename (in outdir)")
    p.add_argument("--json", default="results.json", help="JSON filename (in outdir)")
    p.add_argument("--tls", action="store_true", help="use TLS (wrap TCP socket) - set port to 5061 if not provided")
    p.add_argument("--show-raw", "-R", action="store_true", help="print raw SIP response(s) to console")
    p.add_argument("--only-noauth", action="store_true", help="when used with --show-raw, only print raw when result == NO_AUTH")
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
    print(f"# probes: {len(ips)}, proto: {args.proto}, port: {port}, timeout: {args.timeout}, tls: {args.tls}")

    ensure_dir(args.outdir)
    raw_dir = os.path.join(args.outdir, "raw_responses")
    ensure_dir(raw_dir)

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
            reason = (res.get("reason") or "").replace("\n", " ").replace(",", ";")[:300]
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
                    fh.write(f"# proto: {args.proto}, port: {port}, tls: {args.tls}\n\n")
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
