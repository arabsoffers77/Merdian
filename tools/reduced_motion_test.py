#!/usr/bin/env python3
"""Reduced-motion audit: emulate prefers-reduced-motion, verify zero hidden content."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

PORT = 9346
PROFILE = r'C:\Users\ASUS\AppData\Local\Temp\mec-ox2-rm'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
BASE = 'http://127.0.0.1:8123'
PAGES = ['index', 'about', 'services', 'projects', 'disciplines', 'contact']


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
    def recv(self):
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
                    return payload.decode('utf-8', 'replace')
            chunk = self.sock.recv(65536)
            if not chunk: raise RuntimeError('ws closed')
            self.buf += chunk
    def cmd(self, method, params=None):
        self.mid += 1; myid = self.mid
        self.send(json.dumps({'id': myid, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(self.recv())
            if msg.get('id') == myid: return msg


def run(page):
    proc = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        f'--remote-debugging-port={PORT}', f'--user-data-dir={PROFILE}-{page}',
        '--window-size=500,1000', 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws_url = None
    for _ in range(60):
        try:
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json'))
            pages = [t for t in tabs if t.get('type') == 'page']
            if pages: ws_url = pages[0]['webSocketDebuggerUrl']; break
        except Exception: pass
        time.sleep(0.5)
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
    # emulate reduced motion BEFORE page scripts run
    ws.cmd('Emulation.setEmulatedMedia',
           {'features': [{'name': 'prefers-reduced-motion', 'value': 'reduce'}]})
    ws.cmd('Page.navigate', {'url': f'{BASE}/{page}.html'})
    time.sleep(3.5)
    r = ws.cmd('Runtime.evaluate', {'expression': """(() => {
      const total = document.querySelectorAll('[data-reveal],[data-reveal-child]').length;
      const hidden = Array.from(document.querySelectorAll('[data-reveal],[data-reveal-child]'))
        .filter(el => parseFloat(getComputedStyle(el).opacity) < 0.95).length;
      const rm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const hm = document.querySelector('.hero-media');
      return JSON.stringify({total, hidden, rm,
        heroW: hm ? Math.round(hm.getBoundingClientRect().width) : -1});
    })()""", 'returnByValue': True})
    print(page, '->', r['result']['result'].get('value'))
    proc.kill()


if __name__ == '__main__':
    import shutil
    for d in os.listdir(r'C:\Users\ASUS\AppData\Local\Temp'):
        if d.startswith('mec-ox2-rm'):
            shutil.rmtree(os.path.join(r'C:\Users\ASUS\AppData\Local\Temp', d), ignore_errors=True)
    for pg in PAGES:
        run(pg)
