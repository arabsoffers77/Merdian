#!/usr/bin/env python3
"""CDP screenshot runner: authoritative render proof for local static sites.

Usage:
    python cdp_shot.py
Edit the TARGETS list below (tag, url, filename, mobile?).

Launches headless Chrome with --remote-debugging-port, connects with a minimal
stdlib WebSocket client, sets mobile/desktop viewport via Emulation, waits for
settle, saves Page.captureScreenshot PNGs into _verify/, and prints a
computed-style probe of '.nav-toggle' as a cross-check.

No third-party dependencies. Chrome path is Windows-typical; adjust CHROME if needed.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.parse as up
import urllib.request

PORT = 9339
PROFILE = r'C:\Users\ASUS\AppData\Local\Temp\mec-cdp-profile'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
OUT = r'C:\Users\ASUS\mec-website\_verify'

TARGETS = [
    ('toggle', 'http://127.0.0.1:8422/_verify/toggle-test2.html', 'cdp-toggle.png', True),
    ('home-mobile', 'http://127.0.0.1:8422/index.html', 'cdp-home-mobile.png', True),
    ('home-desktop', 'http://127.0.0.1:8422/index.html', 'cdp-home-desktop.png', False),
]


def run_target(url_tag, target, fname, mobile):
    proc = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={PROFILE}-{url_tag}',
        '--window-size=500,1000', target,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws_url = None
    for _ in range(60):
        try:
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json'))
            pages = [t for t in tabs if t.get('type') == 'page']
            if pages:
                ws_url = pages[0]['webSocketDebuggerUrl']
                break
        except Exception:
            pass
        time.sleep(0.5)
    if not ws_url:
        print(url_tag, ': NO CDP ENDPOINT')
        proc.kill()
        return

    p = up.urlparse(ws_url)
    sock = socket.create_connection((p.hostname, p.port))
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f'GET {p.path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\n'
           'Upgrade: websocket\r\nConnection: Upgrade\r\n'
           f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
    sock.sendall(req.encode())
    while b'\r\n\r\n' not in (resp := resp + sock.recv(4096) if 'resp' in dir() else sock.recv(4096)):
        pass

    buf = b''
    mid = 0

    def ws_send(payload):
        data = payload.encode()
        header = bytearray([0x81])
        n = len(data)
        mask = os.urandom(4)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack('>H', n)
        else:
            header.append(0x80 | 127)
            header += struct.pack('>Q', n)
        header += mask
        sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def ws_recv():
        nonlocal buf
        while True:
            if len(buf) >= 2:
                b1 = buf[1]
                ln = b1 & 0x7F
                off = 2
                if ln == 126:
                    if len(buf) < 4:
                        buf += sock.recv(65536); continue
                    ln = struct.unpack('>H', buf[2:4])[0]; off = 4
                elif ln == 127:
                    if len(buf) < 10:
                        buf += sock.recv(65536); continue
                    ln = struct.unpack('>Q', buf[2:10])[0]; off = 10
                if len(buf) >= off + ln:
                    payload = buf[off:off + ln]
                    buf = buf[off + ln:]
                    return payload.decode('utf-8', 'replace')
            chunk = sock.recv(65536)
            if not chunk:
                raise RuntimeError('ws closed')
            buf += chunk

    def cmd(method, params=None):
        nonlocal mid
        mid += 1
        ws_send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(ws_recv())
            if msg.get('id') == mid:
                return msg

    cmd('Page.enable')
    cmd('Runtime.enable')
    if mobile:
        cmd('Emulation.setDeviceMetricsOverride',
            {'width': 390, 'height': 844, 'deviceScaleFactor': 2, 'mobile': True})
    else:
        cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1440, 'height': 1000, 'deviceScaleFactor': 1, 'mobile': False})
    time.sleep(3.5)

    shot = cmd('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(OUT, fname), 'wb') as f:
        f.write(base64.b64decode(shot['result']['data']))
    print(url_tag, '-> saved', fname)

    probe = cmd('Runtime.evaluate', {
        'expression': ("(() => { const t = document.querySelector('.nav-toggle');"
                       " if (!t) return 'NO TOGGLE'; const cs = getComputedStyle(t);"
                       " const s = t.querySelector('.bars span');"
                       " return JSON.stringify({disp: cs.display,"
                       " rect: t.getBoundingClientRect().toJSON(),"
                       " spanBg: s ? getComputedStyle(s).backgroundColor : null}); })()")})
    print('   probe:', json.loads(probe['result']['result']['value']))

    proc.kill()
    try:
        sock.close()
    except Exception:
        pass


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for t in TARGETS:
        run_target(*t)
