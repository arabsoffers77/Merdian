#!/usr/bin/env python3
"""Clipping regression: at 3 viewport widths, sample typewriter texts through
full cycles; assert every visible state is a complete word (or its prefix only
while the caret is mid-type of a word that FITS). The bug: truncated words at
line edge. Fix: fit-check flips to delete before overflow."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
BASE = 'http://127.0.0.1:8123'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'
OUT = r'D:\work\merdian\ox 2\_verify'
WORDS = ["feasibility studies.", "detailed engineering design.", "construction supervision.",
         "urban planning.", "traffic impact studies."]


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
    profile = os.path.join(TMP, 'mec-ox2-clip-%d' % (time.time() * 1000 % 1e9))
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


if __name__ == '__main__':
    try:
        urllib.request.urlopen(BASE + '/index.html', timeout=2)
    except Exception:
        srv = subprocess.Popen(['python', '-m', 'http.server', '8123', '--bind', '127.0.0.1'],
                               cwd=r'D:\work\merdian\ox 2',
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)

    all_ok = True
    for w in (1440, 1100, 900):          # 900px is where the user saw the clip
        proc, ws = connect(BASE + '/contact.html')
        ws.cmd('Emulation.setDeviceMetricsOverride',
               {'width': w, 'height': 950, 'deviceScaleFactor': 1, 'mobile': False})
        deadline = time.time() + 15
        while time.time() < deadline:
            if ws.js("!!document.querySelector('[data-typewriter]')"):
                break
            time.sleep(0.4)
        # line must never wrap (single-line lock still holds)
        one_line = bool(ws.js(
            "document.querySelector('.type-line').offsetHeight <= "
            "Math.ceil(parseFloat(getComputedStyle(document.querySelector('.type-line')).fontSize) * 1.8)"))
        # image height constant?
        h0 = int(ws.js("Math.round(document.querySelector('.page-hero-media').getBoundingClientRect().height)"))

        bad_clips = []
        completed = set()
        prev = ''
        deadline = time.time() + 15
        while time.time() < deadline:
            t = ws.js("document.querySelector('[data-typewriter]').textContent") or ''
            # a visible text is BAD if it's a strict prefix (>4 chars) of a word AND the full word would overflow
            for word in WORDS:
                if t and word.startswith(t) and len(t) > 4 and t != word:
                    # mid-typing; check whether this prefix already overflows the line
                    over = ws.js(f"""(() => {{
                      const el = document.querySelector('[data-typewriter]');
                      const line = el.closest('.type-line');
                      const probe = document.createElement('span');
                      probe.style.cssText='position:absolute;visibility:hidden;white-space:nowrap;';
                      probe.style.font = getComputedStyle(el).font;
                      probe.textContent = 'Talk to us about\\u00A0' + {json.dumps(t)};
                      line.appendChild(probe);
                      const w2 = probe.getBoundingClientRect().width;
                      line.removeChild(probe);
                      return w2 > line.clientWidth - 6;
                    }})()""")
                    if over:
                        bad_clips.append(t)
            if t in WORDS:
                completed.add(t)
            prev = t
            time.sleep(0.25)

        h1 = int(ws.js("Math.round(document.querySelector('.page-hero-media').getBoundingClientRect().height)"))
        ok = one_line and not bad_clips and len(completed) >= 2 and h0 == h1
        all_ok = all_ok and ok
        print(f'{w}px: singleLine={one_line}, badClips={bad_clips or "none"}, '
              f'completedWords={sorted(completed)}, imgStable={h0==h1}({h0}) -> {"PASS" if ok else "FAIL"}')
        if w == 900:
            shot = ws.cmd('Page.captureScreenshot', {'format': 'png'})
            with open(os.path.join(OUT, 'ox2-contact-noclip.png'), 'wb') as fh:
                fh.write(base64.b64decode(shot['result']['data']))
        proc.kill()
    print('CLIP REGRESSION:', 'ALL PASS' if all_ok else 'FAIL')
