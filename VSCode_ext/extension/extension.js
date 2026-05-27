// ============================================================
// Security Awareness Calculator — VSCode Extension
// Security Awareness PoC — For authorised testing only.
//
// This extension demonstrates that VSCode extensions execute
// with full local user privileges and without sandboxing.
// Upon installation calc.exe is launched as a visible
// indicator of arbitrary code execution.
//
// The author takes no responsibility for any damage or legal
// consequences resulting from misuse of this tool.
//
// https://github.com/0xsyr0/Security-Awareness-Calculator
// ============================================================

const { execSync } = require('child_process');

function activate(context) {
    execSync('calc.exe');
}

function deactivate() {}

module.exports = { activate, deactivate };
