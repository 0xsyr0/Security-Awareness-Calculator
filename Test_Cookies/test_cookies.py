# ============================================================
# Security Awareness Calculator — Cookie Test Script
# Standalone diagnostic tool for verifying Firefox cookie
# extraction on the demo VM. Run with Firefox
# closed via File -> Exit before executing.
#
# Usage: python test_cookies.py
#
# https://github.com/0xsyr0/Security-Awareness-Calculator
# ============================================================

import sqlite3, os, shutil, glob

profile_dir = os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles')
profiles    = glob.glob(os.path.join(profile_dir, '*.default-release'))
if not profiles:
    profiles = glob.glob(os.path.join(profile_dir, '*'))

if not profiles:
    print('[-] No Firefox profile found')
    exit()

print(f'[+] Profile: {profiles[0]}')

cf = os.path.join(profiles[0], 'cookies.sqlite')
ct = os.path.join(os.path.expandvars('%TEMP%'), 'ff_ck.db')

shutil.copy2(cf, ct)
conn = sqlite3.connect(ct)
cur  = conn.cursor()

cur.execute('SELECT COUNT(*) FROM moz_cookies')
print(f'[+] Total cookies: {cur.fetchone()[0]}')

cur.execute('SELECT DISTINCT host FROM moz_cookies ORDER BY host')
print(f'[+] Hosts: {[r[0] for r in cur.fetchall()]}')

cur.execute('SELECT host,name,value FROM moz_cookies ORDER BY host')
print('\n[+] All cookies:')
for r in cur.fetchall():
    print(f'  {r[0]} | {r[1]} | {r[2][:80]}')

conn.close()
os.remove(ct)
