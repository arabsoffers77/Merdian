#!/usr/bin/env python3
"""Verify typewriter (contact) cycles words, and globe-flash (about) settles."""
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
    profile = os.path.join(TMP, 'mec-ox2-fx-%d' % (time.time() * 1000 % 1e9))
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

    # ---- typewriter ----
    proc, ws = connect(BASE + '/contact.html')
    ok_page = None
    deadline = time.time() + 15
    while time.time() < deadline and not ok_page:
        ok_page = ws.js("!!document.querySelector('[data-typewriter]')")
        time.sleep(0.4)
    seen = set()
    states = []
    deadline = time.time() + 14   # ~2 full cycles
    while time.time() < deadline:
        v = ws.js("document.querySelector('[data-typewriter]').textContent")
        if v is not None:
            seen.add(v)
            states.append(v)
        time.sleep(0.35)
    grew_shrank = any(len(b) > len(a) for a, b in zip(states, states[1:])) and \
                  any(len(b) < len(a) for a, b in zip(states, states[1:]))
    print('TYPEWRITER distinct texts:', sorted(seen))
    print('TYPEWRITER types & deletes:', grew_shrank,
          'PASS' if grew_shrank and len(seen) >= 3 else 'FAIL')
    # screenshot mid-type
    shot = ws.cmd('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(OUT, 'ox2-typewriter.png'), 'wb') as fh:
        fh.write(base64.b64decode(shot['result']['data']))
    proc.kill()

    # ---- globe flash ----
    proc, ws = connect(BASE + '/about.html')
    ok_page = None
    deadline = time.time() + 15
    while time.time() < deadline and not ok_page:
        ok_page = ws.js("!!document.querySelector('[data-globe]')")
        time.sleep(0.4)
    ws.js("document.querySelector('[data-globe]').scrollIntoView({block:'center'})")
    deadline = time.time() + 8
    val = None
    while time.time() < deadline:
        val = ws.js("document.querySelector('.gf-word').textContent")
        if val and 'Europe, USA' in val:
            break
        time.sleep(0.4)
    settled = bool(val and 'Europe, USA, Asia & Africa' in val)
    over = int(ws.js("document.documentElement.scrollWidth - document.documentElement.clientWidth"))
    print('GLOBE settled text:', repr(val), '| pageOverX:', over,
          'PASS' if settled and over == 0 else 'FAIL')
    proc.kill()
