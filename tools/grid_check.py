#!/usr/bin/env python3
"""Verify the wrapping timeline grid: all 5 cards visible at once at every width,
zero page overflow, flip still works, screenshots for visual proof."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse, shutil

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


def connect(url):
    profile = os.path.join(TMP, 'mec-ox2-grid-%d' % (time.time() * 1000 % 1e9))
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


def settle_static(proc, ws, w, h, url):
    """Re-navigate with reduced-motion emulated so reveals are instant & final."""
    ws.cmd('Emulation.setEmulatedMedia',
           {'features': [{'name': 'prefers-reduced-motion', 'value': 'reduce'}]})
    ws.cmd('Emulation.setDeviceMetricsOverride',
           {'width': w, 'height': h, 'deviceScaleFactor': w < 800 and 2 or 1, 'mobile': w < 800})
    ws.cmd('Page.navigate', {'url': url})
    deadline = time.time() + 20
    while time.time() < deadline:
        if ws.js("document.querySelectorAll('.flip-card').length === 5"):
            break
        time.sleep(0.4)
    time.sleep(1.5)
    ws.js("document.querySelector('.timeline').scrollIntoView({block:'center'})")
    try:
        ws.js('new Promise(r => setTimeout(r, 1500))', await_promise=True)
    except Exception:
        pass


PROBE = """(() => {
  const row = document.querySelector('.timeline');
  const cards = Array.from(document.querySelectorAll('.flip-card'));
  const doc = document.documentElement;
  const fullyIn = cards.filter(c => { const r = c.getBoundingClientRect();
    return r.left >= -1 && r.right <= doc.clientWidth + 1; }).length;
  return JSON.stringify({
    overX: doc.scrollWidth - doc.clientWidth,
    cardCount: cards.length,
    fullyVisibleNow: fullyIn,
    rowScrollable: row.scrollWidth > row.clientWidth + 2,
    cols: getComputedStyle(row).gridTemplateColumns.split(' ').length
  });
})()"""

SHOTS = [(1440, 1000, 'ox2-flips-desktop.png'), (820, 1180, 'ox2-flips-tablet.png'), (390, 844, 'ox2-flips-mobile.png')]

if __name__ == '__main__':
    SRV = ensure_server()
    all_ok = True
    for w, h, fname in SHOTS:
        proc, ws = connect(BASE + '/about.html')
        settle_static(proc, ws, w, h, BASE + '/about.html')
        probe = json.loads(ws.js(PROBE))
        # flip interaction still works?
        ws.js("document.querySelector('.flip-card').click()")
        time.sleep(0.5)
        flipped = bool(ws.js("document.querySelector('.flip-card').classList.contains('is-flipped')"))
        shot = ws.cmd('Page.captureScreenshot', {'format': 'png'})
        with open(os.path.join(OUT, fname), 'wb') as fh:
            fh.write(base64.b64decode(shot['result']['data']))
        ok = (probe['overX'] == 0 and probe['cardCount'] == 5 and probe['fullyVisibleNow'] == 5
              and not probe['rowScrollable'] and flipped)
        all_ok = all_ok and ok
        print(f"{w}px: {probe} flipped={flipped} -> {'PASS' if ok else 'FAIL'} [{fname}]")
        proc.kill()
    print('WRAPPING GRID:', 'ALL PASS' if all_ok else 'FAILURES PRESENT')
