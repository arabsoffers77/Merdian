#!/usr/bin/env python3
"""CDP screenshot runner for ox 2 build — 6 pages x desktop+mobile into _verify/."""
import base64, json, os, socket, struct, subprocess, time, urllib.request

PORT = 9341
PROFILE = r'C:\Users\ASUS\AppData\Local\Temp\mec-ox2-profile'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
OUT = r'D:\work\merdian\ox 2\_verify'
BASE = 'http://127.0.0.1:8123'
PAGES = ['index', 'about', 'services', 'projects', 'disciplines', 'contact']

TARGETS = []
for pg in PAGES:
    TARGETS.append((pg + '-desktop', f'{BASE}/{pg}.html', f'ox2-{pg}-desktop.png', False))
    TARGETS.append((pg + '-mobile', f'{BASE}/{pg}.html', f'ox2-{pg}-mobile.png', True))


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

    p = urllib.parse.urlparse(ws_url)
    sock = socket.create_connection((p.hostname, p.port))
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f'GET {p.path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\n'
           'Upgrade: websocket\r\nConnection: Upgrade\r\n'
           f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
    sock.sendall(req.encode())
    resp = b''
    while b'\r\n\r\n' not in resp:
        resp += sock.recv(4096)

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
    time.sleep(3.0)
    # keep the page active so GSAP entrance timelines can advance (headless rAF throttle)
    try:
        cmd('Runtime.evaluate', {'expression': 'new Promise(r => setTimeout(r, 2500))',
                                 'awaitPromise': True})
    except Exception:
        pass

    shot = cmd('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(OUT, fname), 'wb') as f:
        f.write(base64.b64decode(shot['result']['data']))
    print(url_tag, '-> saved', fname)

    probe = cmd('Runtime.evaluate', {
        'expression': ("(() => { const t = document.querySelector('.nav-toggle');"
                       " const w = document.querySelectorAll('.hero-title .split-word').length"
                       " || document.querySelectorAll('.page-hero-copy > *').length;"
                       " const r = document.querySelector('.site-header');"
                       " return JSON.stringify({toggle: t ? getComputedStyle(t).display : 'NO TOGGLE',"
                       " animTargets: w,"
                       " headerPos: r ? getComputedStyle(r).position : '?'}); })()")})
    print('   probe:', probe['result']['result'].get('value'))

    proc.kill()
    try:
        sock.close()
    except Exception:
        pass


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    import urllib.parse
    for t in TARGETS:
        run_target(*t)
