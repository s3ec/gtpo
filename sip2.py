#!/usr/bin/env python3
"""
sip_sender_whoami.py
Send SIP MESSAGE and INVITE with User-Agent containing 'whoami'.

Usage:
- Edit the TARGETS list with IPs/ports.
- Choose transport: "UDP" or "TCP"
"""

import socket
import uuid
import time

# ----------------------- CONFIG -----------------------
TARGETS = [
    {"ip": "192.0.2.10", "port": 5060},
    {"ip": "192.0.2.11", "port": 5060},
]

TRANSPORT = "UDP"  # "UDP" or "TCP"
LOCAL_IP = "0.0.0.0"
LOCAL_PORT = 5061  # local port for binding; ephemeral OK
FROM_USER = "alice"
FROM_DOMAIN = "example.com"
TO_USER = "bob"
TO_DOMAIN = "example.net"
# ------------------------------------------------------

def gen_branch():
    return "z9hG4bK" + uuid.uuid4().hex[:8]

def gen_call_id():
    return uuid.uuid4().hex + "@" + (socket.gethostname() or "localhost")

def build_sip_message_body(text):
    return text if isinstance(text, str) else str(text)

def build_message_request(from_user, from_domain, to_user, to_domain, call_id=None, cseq=1, body="Hello"):
    call_id = call_id or gen_call_id()
    branch = gen_branch()
    from_tag = uuid.uuid4().hex[:8]
    via = f"SIP/2.0/{TRANSPORT} {LOCAL_IP}:{LOCAL_PORT};branch={branch}"
    from_hdr = f"<sip:{from_user}@{from_domain}>;tag={from_tag}"
    to_hdr = f"<sip:{to_user}@{to_domain}>"
    contact = f"<sip:{from_user}@{LOCAL_IP}:{LOCAL_PORT}>"
    body_text = build_sip_message_body(body)
    content_length = len(body_text.encode("utf-8"))

    # Inject 'whoami' literally in User-Agent
    user_agent = "python-sip-sender/1.0 (whoami)"

    request_lines = [
        f"MESSAGE sip:{to_user}@{to_domain} SIP/2.0",
        f"Via: {via}",
        f"Max-Forwards: 70",
        f"From: {from_hdr}",
        f"To: {to_hdr}",
        f"Call-ID: {call_id}",
        f"CSeq: {cseq} MESSAGE",
        f"Contact: {contact}",
        f"User-Agent: {user_agent}",
        f"Content-Type: text/plain; charset=utf-8",
        f"Content-Length: {content_length}",
        "",
        body_text
    ]
    return "\r\n".join(request_lines), call_id

def build_invite_request(from_user, from_domain, to_user, to_domain, call_id=None, cseq=1, sdp=None):
    call_id = call_id or gen_call_id()
    branch = gen_branch()
    from_tag = uuid.uuid4().hex[:8]
    via = f"SIP/2.0/{TRANSPORT} {LOCAL_IP}:{LOCAL_PORT};branch={branch}"
    from_hdr = f"<sip:{from_user}@{from_domain}>;tag={from_tag}"
    to_hdr = f"<sip:{to_user}@{to_domain}>"
    contact = f"<sip:{from_user}@{LOCAL_IP}:{LOCAL_PORT}>"

    if sdp is None:
        sdp_lines = [
            "v=0",
            f"o={from_user} 0 0 IN IP4 {LOCAL_IP}",
            "s=-",
            f"c=IN IP4 {LOCAL_IP}",
            "t=0 0",
            "m=audio 4000 RTP/AVP 0 8 101",
            "a=rtpmap:0 PCMU/8000",
            "a=rtpmap:8 PCMA/8000",
            "a=rtpmap:101 telephone-event/8000",
            "a=fmtp:101 0-16",
            "a=sendrecv"
        ]
        sdp = "\r\n".join(sdp_lines) + "\r\n"

    content_length = len(sdp.encode("utf-8"))
    user_agent = "python-sip-sender/1.0 (whoami)"

    request_lines = [
        f"INVITE sip:{to_user}@{to_domain} SIP/2.0",
        f"Via: {via}",
        f"Max-Forwards: 70",
        f"From: {from_hdr}",
        f"To: {to_hdr}",
        f"Call-ID: {call_id}",
        f"CSeq: {cseq} INVITE",
        f"Contact: {contact}",
        f"User-Agent: {user_agent}",
        f"Content-Type: application/sdp",
        f"Content-Length: {content_length}",
        "",
        sdp
    ]
    return "\r\n".join(request_lines), call_id

def send_request(msg, target_ip, target_port):
    if TRANSPORT.upper() == "UDP":
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    else:  # TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        if TRANSPORT.upper() == "TCP":
            sock.connect((target_ip, target_port))
            sock.send(msg.encode())
            try:
                resp = sock.recv(4096)
                return resp.decode(errors="ignore")
            except socket.timeout:
                return None
        else:
            sock.sendto(msg.encode(), (target_ip, target_port))
            try:
                resp, addr = sock.recvfrom(4096)
                return resp.decode(errors="ignore")
            except socket.timeout:
                return None
    finally:
        sock.close()

def main():
    print("=== SIP sender with 'whoami' in User-Agent ===\n")
    for target in TARGETS:
        ip = target["ip"]
        port = target["port"]
        print(f"Target: {ip}:{port}\n")

        # Send MESSAGE
        msg_req, _ = build_message_request(FROM_USER, FROM_DOMAIN, TO_USER, TO_DOMAIN, body="Hello SIP")
        print(">>> Sending SIP MESSAGE")
        resp = send_request(msg_req, ip, port)
        print(resp if resp else "No response (timeout)")
        print("\n---\n")

        # Send INVITE
        invite_req, _ = build_invite_request(FROM_USER, FROM_DOMAIN, TO_USER, TO_DOMAIN)
        print(">>> Sending SIP INVITE")
        resp = send_request(invite_req, ip, port)
        print(resp if resp else "No response (timeout)")
        print("\n===\n")

if __name__ == "__main__":
    main()
