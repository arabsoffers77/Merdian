#!/usr/bin/env python3
"""Verify: timeline scrollbar visually hidden, drag-scroll still works,
edge-fade classes toggle, and no page-level horizontal overflow anywhere."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse, shutil

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
BASE = 'http://127.0.0.1:8123'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'


class WS:
    def __init__(self, sock):
        self.sock = sock; self.buf = b''; self.mid = 0
    def send(self, payload):
        data = payload.encode(); header = bytearray([0x81]); n = len(data); mask = os.urandom(4)
        if n < 126: header.append(0x80 | n)
        elif n < 65536: header.append(0x80 | 126); header += struct.pack('>H', n)
        else: header.append(0x80 | 127); header += struct.pack('>Q', n)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
    def recv_raw(self):
        while True:
            if len(self.buf) >= 2:
                b1 = self.buf[1]; ln = b1 & 0x7F; off = 2
                if ln == 126:
                    if len(self.buf) < 4: self.buf += self.sock.recv(65536); continue
                    ln = struct.unpack('>H', self.buf[2:4])[0]; off = 4
                elif ln == 127:
                    if len(self.buf) < 10: self.buf += self.sock.recv(65536); continue
                    ln = struct.unpack('>Q', self.buf[2:10])[0]; off = 10
                if len(self.buf) >= off + ln:
                    payload = self.buf[off:off + ln]; self.buf = self.buf[off + ln:]
                    return json.loads(payload.decode('utf-8', 'replace'))
            chunk = self.sock.recv(65536)
            if not chunk: raise RuntimeError('ws closed')
            self.buf += chunk
    def cmd(self, method, params=None):
        self.mid += 1; myid = self.mid
        self.send(json.dumps({'id': myid, 'method': method, 'params': params or {}}))
        while True:
            msg = self.recv_raw()
            if msg.get('id') == myid: return msg
    def js(self, expr):
        r = self.cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        return r.get('result', {}).get('result', {}).get('value')


def connect(url):
    profile = os.path.join(TMP, 'mec-ox2-tl-%d' % (time.time() * 1000 % 1e9))
    proc = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        '--remote-debugging-port=0', f'--user-data-dir={profile}', url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    port = None
    deadline = time.time() + 30
    while time.time() < deadline:
        f = os.path.join(profile, 'DevToolsActivePort')
        if os.path.exists(f):
            try:
                port = int(open(f).read().split('\n')[0].strip()); break
            except Exception:
                pass
        time.sleep(0.3)
    ws_url = None
    for _ in range(40):
        try:
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
            pages = [t for t in tabs if t.get('type') == 'page']
            if pages: ws_url = pages[0]['webSocketDebuggerUrl']; break
        except Exception:
            pass
        time.sleep(0.4)
    p = urllib.parse.urlparse(ws_url)
    sock = socket.create_connection((p.hostname, p.port))
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f'GET {p.path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\n'
           'Upgrade: websocket\r\nConnection: Upgrade\r\n'
           f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
    sock.sendall(req.encode())
    resp = b''
    while b'\r\n\r\n' not in resp: resp += sock.recv(4096)
    ws = WS(sock)
    ws.cmd('Page.enable'); ws.cmd('Runtime.enable')
    return proc, ws


def ensure_server():
    try:
        urllib.request.urlopen(BASE + '/index.html', timeout=2)
        print('server: up'); return None
    except Exception:
        pass
    srv = subprocess.Popen(['python', '-m', 'http.server', '8123', '--bind', '127.0.0.1'],
                           cwd=r'D:\work\merdian\ox 2',
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            urllib.request.urlopen(BASE + '/index.html', timeout=2)
            print('server: started'); return srv
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('no server')


if __name__ == '__main__':
    SRV = ensure_server()
    proc, ws = connect(BASE + '/about.html')
    ok_page = None
    deadline = time.time() + 20
    while time.deadline_ok if False else time.time() < deadline:
        ok_page = ws.js("document.querySelectorAll('.flip-card').length === 5")
        if ok_page: break
        time.sleep(0.4)

    # scroll timeline into view so layout is settled
    ws.js("document.querySelector('.timeline').scrollIntoView({block:'center'})")
    time.sleep(2)

    checks = {}
    checks['scrollbarWidthNone'] = ws.js(
        "getComputedStyle(document.querySelector('.timeline')).scrollbarWidth === 'none'")
    checks['webkitRule'] = ws.js(
        "!!Array.from(document.styleSheets).some(s => { try { return Array.from(s.cssRules).some(r => r.selectorText && r.selectorText.includes('.timeline::-webkit-scrollbar')); } catch(e){ return false; } })")
    checks['wrapOverflowing'] = bool(ws.js(
        "document.querySelector('[data-timeline-wrap]').classList.contains('is-overflowing')"))
    checks['startFaded'] = bool(ws.js(
        "document.querySelector('[data-timeline-wrap]').classList.contains('is-scrolled-start')"))

    # simulate a drag/swipe: scrollLeft change must work & update edge classes
    ws.js("document.querySelector('.timeline').scrollLeft = 300")
    time.sleep(0.6)
    checks['scrolled'] = int(ws.js("document.querySelector('.timeline').scrollLeft")) >= 250
    checks['endFadeCleared'] = bool(ws.js(
        "!document.querySelector('[data-timeline-wrap]').classList.contains('is-scrolled-end')"))
    checks['startNowVisible'] = bool(ws.js(
        "!document.querySelector('[data-timeline-wrap]').classList.contains('is-scrolled-start')"))
    ws.js("document.querySelector('.timeline').scrollLeft = 9999")
    time.sleep(0.6)
    checks['endAtFarRight'] = bool(ws.js(
        "document.querySelector('[data-timeline-wrap]').classList.contains('is-scrolled-end')"))

    # page-level overflow still zero at all widths
    overflows = {}
    for w in (1440, 768, 390):
        ws.cmd('Emulation.setDeviceMetricsOverride',
               {'width': w, 'height': 1000, 'deviceScaleFactor': 1, 'mobile': w < 800})
        time.sleep(0.8)
        overflows[w] = int(ws.js("document.documentElement.scrollWidth - document.documentElement.clientWidth"))

    flip_n = int(ws.js("document.querySelectorAll('.flip-card').length"))
    all_ok = (all(v is True or v is True for k, v in checks.items() if k != 'startFaded')
              and checks['scrollbarWidthNone'] and checks['webkitRule']
              and checks['wrapOverflowing'] and checks['startFaded'] and checks['scrolled']
              and checks['startNowVisible'] and checks['endAtFarRight'] and flip_n == 5
              and all(v == 0 for v in overflows.values()))
    for k, v in checks.items():
        print(f'{k}: {v}')
    print('pageOverX:', overflows, '| flipCards:', flip_n)
    print('TIMELINE FIX:', 'PASS' if all_ok else 'FAIL')
    proc.kill()
