#!/usr/bin/env python3
"""Horizontal-overflow audit: measure document.scrollWidth vs clientWidth
on every page at desktop + mobile widths, and identify offending elements."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse, shutil

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
BASE = 'http://127.0.0.1:8123'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'
PAGES = ['index', 'about', 'services', 'projects', 'disciplines', 'contact']
WIDTHS = [(1440, 1000), (768, 1000), (390, 844)]


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
        urllib.request.urlopen(BASE + '/index.html', timeout=2)
        return None
    except Exception:
        pass
    srv = subprocess.Popen(['python', '-m', 'http.server', '8123', '--bind', '127.0.0.1'],
                           cwd=r'D:\work\merdian\ox 2',
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            urllib.request.urlopen(BASE + '/index.html', timeout=2)
            return srv
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('no server')


PROBE = """(() => {
  const doc = document.documentElement;
  const overX = doc.scrollWidth - doc.clientWidth;
  const bad = [];
  if (overX > 1) {
    const vw = doc.clientWidth;
    document.querySelectorAll('body *').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.right > vw + 1 && r.width > 24 && !el.closest('.ticker') ) {
        const cls = (typeof el.className === 'string' && el.className) ? '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : '';
        bad.push(el.tagName.toLowerCase() + cls + '@' + Math.round(r.right));
      }
    });
  }
  return JSON.stringify({overX, offenders: bad.slice(0, 6),
    timelineScrollable: (() => { const t = document.querySelector('.timeline');
      return t ? (t.scrollWidth > t.clientWidth ? t.scrollWidth - t.clientWidth : 0) : -1; })()});
})()"""


def run(page, w, h):
    profile = os.path.join(TMP, f'mec-ox2-of-{page}-{w}')
    shutil.rmtree(profile, ignore_errors=True)
    proc = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        '--remote-debugging-port=0', f'--user-data-dir={profile}', f'{BASE}/{page}.html',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
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
        deadline = time.time() + 25
        while time.time() < deadline and not ws_url:
            try:
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
                pages = [t for t in tabs if t.get('type') == 'page']
                if pages: ws_url = pages[0]['webSocketDebuggerUrl']
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
        ws.cmd('Emulation.setDeviceMetricsOverride',
               {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': w < 800})
        time.sleep(2.5)
        val = ws.js(PROBE)
        print(f'{page}@{w}: {val}')
        proc.kill()
    finally:
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == '__main__':
    SRV = ensure_server()
    for pg in PAGES:
        for w, h in WIDTHS:
            run(pg, w, h)
