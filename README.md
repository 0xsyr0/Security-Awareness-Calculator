<p align="center">
  <img width="300" height="300" src="/Images/Security-Awareness-Calculator.png">
</p>

# Security Awareness Calculator

## ⚠️ DISCLAIMER

This repository contains security awareness tooling developed strictly for
authorised penetration testing, red team engagements, and internal security
awareness demonstrations. All tools are provided for **educational and demo
purposes only**.

**This tooling is not built with OPSEC in mind and is intended solely for
controlled demo environments.**

**The author takes no responsibility for any damage, data loss, or legal
consequences resulting from the use or misuse of any tool contained in this
repository. By using any component of this repository you accept full
responsibility for your actions.**

Only use these tools on systems you own or have explicit written authorisation
to test. Unauthorised use is illegal in most jurisdictions.

---

## Background and Motivation

This project exists because the attacks it demonstrates are no longer
theoretical. The following real-world incidents directly motivated the creation
of this tooling and form the narrative backbone of the security awareness
session it was built to support.

### Shai-Hulud and Mini Shai-Hulud (2025–2026)

Between September 2025 and May 2026, a threat actor tracked as **TeamPCP**
(also tracked by Google's Threat Intelligence Group as UNC6780) conducted a
sustained series of coordinated software supply chain attacks across the npm
and PyPI ecosystems under a campaign they call **Shai-Hulud**.

The campaign centres on a self-propagating worm that steals developer and cloud
credentials, then uses those credentials to publish poisoned versions of
additional packages — turning the software supply chain itself into a
propagation mechanism. Each compromised CI/CD pipeline becomes a new
distribution vector, enabling exponential spread without further attacker
input.

The worm has evolved across three generations:

- **Shai-Hulud** (September 2025) — the original variant. First
  self-replicating malware observed in the npm ecosystem. Harvested maintainer
  tokens and used them to publish poisoned packages automatically.
- **Shai-Hulud 2.0 / SHA1-Hulud** (November 2025) — added wiper
  functionality and improved credential harvesting scope. Microsoft published
  detection and response guidance in December 2025.
- **Mini Shai-Hulud** (April–May 2026) — the current generation. Named after
  a signature embedded in the malware's exfiltration infrastructure: newly
  created GitHub repositories on victim accounts carry the description
  *"A Mini Shai-Hulud has Appeared"*, a reference to the sandworms in Dune.
  This variant achieved a critical first by compromising packages carrying
  valid SLSA Build Level 3 provenance attestations, proving that process
  integrity controls can be defeated.

Confirmed victims include TanStack (React Router — over 12 million weekly
downloads), UiPath, MistralAI, Aqua's Trivy security scanner, CheckMarx's
KICS, the LiteLLM library, the Telnyx SDK, AntV, and others. Downstream impact
included breaches affecting the European Commission's public website, Mercor,
and two OpenAI employee devices.

The campaign injected persistence into AI coding agent configurations —
specifically `.claude/settings.json` SessionStart hooks and
`.vscode/tasks.json` folderOpen triggers — ensuring malware re-execution on
every developer session regardless of whether the original package infection
was later remediated.

### The GitHub Breach (May 2026)

The most direct motivation for this project: **GitHub was breached after one
of its developers installed a malicious VSCode extension**. TeamPCP claimed
access to approximately 4,000 GitHub code repositories and offered the
material for sale on BreachForums. GitHub confirmed at least 3,800 compromised
repositories containing GitHub's own source code.

The attack vector was straightforward — a developer installed a trojanised
VSCode extension, the extension harvested credentials, and those credentials
propagated the infection outward through the supply chain. No zero-day
exploits, no sophisticated malware delivery infrastructure. A VSCode extension.

This is why this project exists. The VSCode extension attack surface is
widely misunderstood by developers and IT staff alike. Most people assume
that installing an extension from a trusted-looking source is safe. It is not.

### Why VSCode Extensions Are Dangerous

VSCode extensions execute with the full privileges of the logged-in user.
There is no sandboxing, no permission model, no capability restriction. An
extension can read the filesystem, execute arbitrary processes, make network
connections, and persist across reboots — all silently, all on installation,
without any user interaction beyond clicking install.

The `activationEvents: ["*"]` manifest field causes an extension to activate
immediately on install and on every subsequent VSCode startup. The attack
surface is the install prompt itself.

---

## OPSEC Notice

This tooling is **not built with OPSEC in mind** and is intended solely for
controlled demo environments. The following known weaknesses are intentional
for demonstration clarity and must be understood before use:

- **Unencrypted C2 communication** — all traffic between the implant and
  `c2.py` is transmitted in plaintext over a raw TCP socket. No TLS, no
  traffic obfuscation, no domain fronting. Any network monitoring solution
  will trivially identify and capture the session.
- **Cleartext length-prefix framing** — commands and responses are framed with
  a 4-byte big-endian length header. This is a well-known protocol pattern
  detectable by IDS/IPS signatures and network-based EDR.
- **No beacon jitter or sleep** — the implant connects immediately and
  maintains a persistent connection. This behaviour is highly anomalous and
  will be flagged by EDR solutions monitoring for persistent outbound
  connections from `Code.exe` or `python.exe`.
- **No process injection or hollowing** — the reverse shell runs as a
  standalone `python.exe` or Node.js process with no attempt to blend into
  legitimate process trees. Parent-child process relationships are trivially
  suspicious.
- **No anti-analysis or sandbox evasion** — no environment checks, VM
  detection, or sleep-based evasion. Any sandbox will detonate the payload
  immediately.
- **No payload encryption or obfuscation** — the base64 encoding used in the
  cookie scripts and stager is encoding only, not encryption, and is trivially
  reversible by any analyst.
- **MAC-address IP obfuscation is cosmetic** — the obfuscation in
  `obfuscator.py` is a simple hex encoding scheme that will not defeat static
  or dynamic analysis. It illustrates the concept of inline decoding for
  educational purposes only.
- **Hardcoded operator values** — `stage.js` and `extension.js` require manual
  replacement of `<IP>` and `<PORT>` placeholders.
  Forgetting to replace these will cause the implant to fail silently.
- **No authentication on C2** — `c2.py` accepts connections from any source.
  Bind it to a specific interface or restrict access via firewall rules during
  demos.
- **Web application is intentionally vulnerable** — `Web_Application/app.py`
  is designed with deliberate security weaknesses: plaintext credential storage
  in session cookies, no `httponly` flag, no `secure` flag, no CSRF
  protection, no rate limiting, no input validation, and hardcoded credentials.
  It must never be deployed outside an isolated demo environment.
- **Firefox-specific cookie extraction** — the cookie stealing functionality
  targets Firefox only. Edge 148+ implements App-Bound Encryption (v20) which
  prevents cookie extraction from non-browser processes. This is a known
  limitation and an intentional talking point about browser security posture
  differences.
- **No cleanup or self-deletion** — the stager writes files to `%TEMP%` and
  does not remove itself after execution. Manual cleanup is required after each
  demo run.
- **Single-session C2** — the C2 handles multiple sessions but has no
  persistent storage, no tasking queue, and no reconnect logic. Sessions lost
  due to network interruption require a full reinstall of the extension.

---

## Repository Structure

```
Security-Awareness-Calculator/
├── Images/                      — extension icon (128x128 PNG)
│   ├── icon.png
│   └── Security_Awareness_Calculator.png
├── Obfuscator/                  — MAC-address IP/port obfuscator
│   └── obfuscator.py
├── SimpleC2/                    — C2 server, weaponized extension, and stager
│   ├── c2.py                    — Python C2 with Firefox cookie stealing
│   ├── extension.js             — weaponized VSCode extension stager template
│   └── stage.js                 — Node.js reverse shell stage (operator template)
├── Test_Cookies/                — standalone Firefox cookie diagnostic tool
│   └── test_cookies.py
├── VSCode_ext/                  — unweaponized PoC extension (pops calc.exe only)
│   ├── [Content_Types].xml
│   ├── extension/
│   │   ├── extension.js
│   │   ├── icon.png
│   │   └── package.json
│   └── extension.vsixmanifest
├── VSCode_ext_weaponized/       — weaponized extension template
│   ├── [Content_Types].xml
│   ├── extension/
│   │   ├── extension.js
│   │   ├── icon.png
│   │   └── package.json
│   └── extension.vsixmanifest
└── Web_Application/             — insecure demo web app for session theft
    └── app.py
```

---

## Prerequisites

### Demo VM (Windows)

```cmd
winget install Python.Python.3.12
pip install flask pycryptodome
winget install Mozilla.Firefox
```

Firefox is required for the cookie stealing demonstration. Edge 148+ uses
App-Bound Encryption (v20) which prevents cookie extraction from non-browser
processes. Firefox stores HTTP cookies as plaintext SQLite with no additional
encryption layer.

Firefox must be configured with the following `about:config` values to prevent
cookies being wiped on shutdown:

| Setting | Required value |
|---|---|
| `privacy.sanitize.sanitizeOnShutdown` | `false` |
| `privacy.clearOnShutdown.cookies` | `false` |

### Attacker VM (Kali)

```shell
python3 -m venv venv
source venv/bin/activate
pip install pycryptodome
```

---

## Phase 1 — Unweaponized PoC (`VSCode_ext/`)

### What it does

Immediately launches `calc.exe` on installation. No network connections, no
data collection, no persistence. Demonstrates that VSCode extensions execute
with full local user privileges and without sandboxing. The calculator popup
serves as a safe, visible, and easily understood indicator of arbitrary code
execution in the context of the logged-in user.

### Building

No npm required — package manually using zip:

```shell
cd VSCode_ext
mkdir -p vsix-build/extension
cp extension/extension.js extension/package.json vsix-build/extension/
cp '[Content_Types].xml' extension.vsixmanifest vsix-build/
cd vsix-build
zip -r ../Security_Awareness_Calculator.vsix . -x "*.DS_Store"
```

Or with vsce:

```shell
npm install -g @vscode/vsce
vsce package --allow-missing-publisher
```

### Icon generation

```shell
cairosvg Icons/icon.svg -o Icons/icon.png -W 128 -H 128
```

Or with Inkscape:

```shell
inkscape Icons/icon.svg --export-filename=Icons/icon.png -w 128 -h 128
```

### `package.json`

```json
{
    "name": "security-awareness-calculator",
    "displayName": "Security Awareness Calculator",
    "description": "⚠️ Security Awareness PoC — For authorised testing only. See https://github.com/0xsyr0/Security-Awareness-Calculator",
    "version": "0.0.1",
    "publisher": "syro",
    "icon": "icon.png",
    "engines": {
        "vscode": "^1.80.0"
    },
    "activationEvents": ["*"],
    "main": "./extension.js",
    "contributes": {}
}
```

### Installing

```cmd
code --install-extension Security_Awareness_Calculator.vsix
```

### Uninstalling

```cmd
code --list-extensions
code --uninstall-extension syro.security-awareness-calculator
```

---

## Phase 2 — Weaponized Extension (`VSCode_ext_weaponized/`)

### What it does

Pops `calc.exe` for visual impact, then fetches and executes `stage.js` from
the operator's HTTP server, establishing a reverse shell to `c2.py`.

### Operator setup — required before use

This template ships non-functional. Replace all placeholders in
`VSCode_ext_weaponized/extension/extension.js` before building:

| Placeholder | Description |
|---|---|
| `<IP>` | Your C2/listener IP address |
| `<PORT>` | Your HTTP server port for stage delivery |

Never commit populated values back to this repository.

### Building

```shell
cd VSCode_ext_weaponized
mkdir -p vsix-build/extension
cp extension/extension.js extension/package.json vsix-build/extension/
cp '[Content_Types].xml' extension.vsixmanifest vsix-build/
cd vsix-build
zip -r ../Security_Awareness_Calculator_Weaponized.vsix . -x "*.DS_Store"
```

### Installing

```cmd
code --install-extension Security_Awareness_Calculator_Weaponized.vsix
```

### Uninstalling

```cmd
code --uninstall-extension syro.security-awareness-calculator-weaponized
```

---

## Phase 3 — Obfuscator and Reverse Shell (`Obfuscator/obfuscator.py`)

Generates a MAC-address obfuscated Python reverse shell payload ready to inject
into a target script on the demo VM. Output is written to `payload.output`.

```shell
python3 Obfuscator/obfuscator.py <IP> <PORT>
python3 Obfuscator/obfuscator.py 192.168.1.100 9001
```

`payload.output` is excluded from the repository via `.gitignore`. Never commit
populated operator values.

---

## Phase 4 — C2 Server (`SimpleC2/c2.py`)

### Running

```shell
source venv/bin/activate

# Terminal 1 — serve stage.js
python3 -m http.server 80

# Terminal 2 — C2 listener
python3 SimpleC2/c2.py
```

### Main menu commands

| Command | Description |
|---|---|
| `sessions` | List all active sessions with alive/dead status |
| `use <id>` | Interact with session by short ID |
| `clear_sessions` | Remove dead sessions from table |
| `help` | Show help menu |
| `quit` | Shut down C2 server |

### Session commands

| Command | Description |
|---|---|
| `steal_cookies` | Steal and decode Firefox session_token cookie |
| `dump_cookies [host]` | Dump all Firefox cookies, optional host filter |
| `debug_cookies` | Dump raw Firefox cookie metadata for diagnosis |
| `whoami` | Current user context and privileges |
| `pwd` | Print current working directory |
| `cd <path>` | Change working directory |
| `dir [path]` | List directory contents |
| `mkdir <path>` | Create directory recursively |
| `type <file>` | Print file contents to screen |
| `writefile <path> <data>` | Write text to file on target |
| `download <path>` | Download file from target to Kali |
| `upload <l> <r>` | Upload local file to remote path |
| `background` | Return to main menu (session stays alive) |
| `exit` | Terminate and close session |
| `<any command>` | Passed directly to cmd.exe on target |

---

## Phase 4 — Web Application (`Web_Application/app.py`)

Simulates an insecure enterprise login portal with a base64-encoded session
cookie containing plaintext credentials. Used to demonstrate session token theft
via Firefox cookie extraction from the filesystem.

```cmd
python app.py
```

Runs on port 5000. Default credentials:

| Username | Password |
|---|---|
| `jdoe` | `Summer2024!` |
| `admin` | `P@ssw0rd123` |

### Demo flow

1. Open Firefox on the demo VM
2. Navigate to `http://127.0.0.1:5000`
3. Log in as `jdoe` or `admin`
4. Close Firefox via **File → Exit** — clean shutdown required for cookie flush
5. From the C2 session run `steal_cookies`
6. Credentials printed in plaintext, curl replay command generated automatically

### Replay session from Kali

```shell
curl -s http://<DEMO_VM_IP>:5000/dashboard \
  -H "Cookie: session_token=<TOKEN>"
```

---

## Cookie Diagnostic Tool (`Test_Cookies/test_cookies.py`)

Standalone script for verifying Firefox cookie extraction works on the demo VM
before running the full C2 demo. Run with Firefox closed via File → Exit.

```cmd
python test_cookies.py
```

---

## `.gitignore`

```
payload.output
*.vsix
__pycache__/
*.pyc
venv/
```

---

## Remediation Recommendations

| Control | Phase |
|---|---|
| VSCode extension allow-listing via Intune/SCCM | 1, 2 |
| Block `vscode://` URI handler via registry policy | 1, 2 |
| Disable `.vsix` installation via `extensions.allowed` policy | 1, 2 |
| Monitor outbound connections originating from `Code.exe` | 2 |
| AppLocker/WDAC restricting script execution from `%TEMP%` | 2, 3 |
| Application control policies for scheduled task scripts | 3 |
| Network monitoring and alerting on raw TCP reverse shells | 2, 3 |
| Rotate all CI/CD secrets and developer tokens after any supply chain incident | 1, 2 |
| Always set `httponly=True` and `secure=True` on session cookies | 4 |
| Never encode credentials into session tokens — use opaque server-side IDs | 4 |
| Enforce browser hardening policies via endpoint management | 4 |
| Use a Chromium-based browser with App-Bound Encryption enabled | 4 |
| Disable Firefox cookie persistence or enforce cookie encryption via policy | 4 |
| Monitor `.vscode/tasks.json` and `.claude/settings.json` for unauthorised modifications | 1, 2 |

---

## Resources

### Shai-Hulud and Mini Shai-Hulud

- [Mini Shai-Hulud FAQ — Tenable](https://www.tenable.com/blog/mini-shai-hulud-frequently-asked-questions)
- [Mini Shai-Hulud: Multi-Ecosystem Developer Supply Chain Attack — Cloud Security Alliance](https://labs.cloudsecurityalliance.org/research/csa-research-note-mini-shai-hulud-multi-ecosystem-supply-cha/)
- [Mini Shai-Hulud malware compromises hundreds of open-source packages — CyberScoop](https://cyberscoop.com/mini-shai-hulud-supply-chain-malware-attack/)
- [Team PCP's Mini Shai-Hulud tears at open-source trust — ReversingLabs](https://www.reversinglabs.com/blog/mini-shai-hulud-tears-at-oss-trust)

### GitHub Breach

- [TeamPCP breached GitHub's internal codebase via poisoned VS Code extension — Help Net Security](https://www.helpnetsecurity.com/2026/05/20/github-breached-teampcp/)
- [TeamPCP Hits GitHub in Supply Chain Attack — Technology Org](https://www.technology.org/2026/05/22/teampcp-github-supply-chain-attack/)
- [GitHub Breach Linked to TeamPCP Supply Chain Attack Spree](https://www.moroccoworldnews.com/2026/05/306024/github-breach-linked-to-teampcp-supply-chain-attack-spree/)

### VSCode Extension Security

- [Leveraging VSCode Extensions for Initial Access — MDSec](https://www.mdsec.co.uk/2023/08/leveraging-vscode-extensions-for-initial-access/)

### General Supply Chain Security

- [Software Supply Chain Security Report 2026 — ReversingLabs](https://www.reversinglabs.com)
- [SLSA Framework — Supply Chain Levels for Software Artifacts](https://slsa.dev)
- [OpenSSF Scorecard — Assessing open source project security](https://securityscorecards.dev)
