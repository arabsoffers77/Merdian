#!/usr/bin/env python3
"""Regression: contact hero image height must stay CONSTANT through the whole
typewriter cycle (the two-line wrap bug), and assoc-flash cycles on About."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
BASE = 'http://127.0.0.1:8123'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'
OUT = r'D:\work\merdian\ox 2\_verify'


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
    profile = os.path.join(TMP, 'mec-ox2-hreg-%d' % (time.time() * 1000 % 1e9))
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
        urllib.request.urlopen(BASE + '/index.html', timeout=2); print('server: up'); return None
    except Exception:
        pass
    srv = subprocess.Popen(['python', '-m', 'http.server', '8123', '--bind', '127.0.0.1'],
                           cwd=r'D:\work\merdian\ox 2',
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            urllib.request.urlopen(BASE + '/index.html', timeout=2); print('server: started'); return srv
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('no server')


if __name__ == '__main__':
    SRV = ensure_server()

    # ---- CONTACT: image height stability across the full typewriter cycle ----
    proc, ws = connect(BASE + '/contact.html')
    heights = []
    texts = []
    deadline = time.time() + 16   # covers type+delete of several words
    while time.time() < deadline:
        h = ws.js("Math.round(document.querySelector('.page-hero-media').getBoundingClientRect().height)")
        t = ws.js("document.querySelector('[data-typewriter]').textContent")
        if h: heights.append(int(h))
        if t is not None: texts.append(t)
        time.sleep(0.4)
    uniq_h = sorted(set(heights))
    line_count_stable = bool(ws.js(
        "(document.querySelector('.type-line').offsetHeight <= "
        "Math.ceil(parseFloat(getComputedStyle(document.querySelector('.type-line')).fontSize) * 1.8))"))
    ok_contact = len(uniq_h) == 1 and line_count_stable
    print(f'CONTACT hero-media heights seen: {uniq_h} (samples={len(heights)}) '
          f'| single-line locked={line_count_stable} -> {"PASS" if ok_contact else "FAIL"}')
    shot = ws.cmd('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(OUT, 'ox2-contact-fixed.png'), 'wb') as fh:
        fh.write(base64.b64decode(shot['result']['data']))
    proc.kill()

    # ---- ABOUT: assoc flash cycles on its own line; paragraph intact ----
    proc, ws = connect(BASE + '/about.html')
    ok_page = None
    deadline = time.time() + 15
    while time.time() < deadline and not ok_page:
        ok_page = ws.js("!!document.querySelector('[data-assoc]')")
        time.sleep(0.4)
    ws.js("document.querySelector('[data-assoc]').scrollIntoView({block:'center'})")
    seen = set()
    deadline = time.time() + 9
    while time.time() < deadline:
        v = ws.js("document.querySelector('.afw').textContent")
        if v: seen.add(v)
        time.sleep(0.35)
    para_intact = bool(ws.js(
        "document.querySelectorAll('.split-2 .lede')[0].textContent.indexOf('Europe, USA, Asia & Africa as necessary') !== -1"))
    over = int(ws.js("document.documentElement.scrollWidth - document.documentElement.clientWidth"))
    ok_about = len(seen) >= 3 and para_intact and over == 0
    print('ABOUT assoc cycled words:', sorted(seen),
          f'| paragraph intact={para_intact}, overX={over} -> {"PASS" if ok_about else "FAIL"}')
    shot = ws.cmd('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(OUT, 'ox2-about-assoc.png'), 'wb') as fh:
        fh.write(base64.b64decode(shot['result']['data']))
    proc.kill()
    print('OVERALL:', 'PASS' if (ok_contact and ok_about) else 'FAIL')
