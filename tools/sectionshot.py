#!/usr/bin/env python3
"""Targeted section captures: scroll each reported section into view, shoot it."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse, shutil

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
OUT = r'D:\work\merdian\ox 2\_verify'
BASE = 'http://127.0.0.1:8123'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'

# tag, url, css selector of section container, out name
TARGETS = [
    ('home-services', f'{BASE}/index.html', '.cells', 'ox2-fix-home-services.png'),
    ('about-flips', f'{BASE}/about.html', '.timeline', 'ox2-fix-about-flips.png'),
    ('projects-grid', f'{BASE}/projects.html', '.projects-grid', 'ox2-fix-projects-grid.png'),
]


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
    def js(self, expr, await_promise=False):
        r = self.cmd('Runtime.evaluate', {'expression': expr, 'awaitPromise': await_promise,
                                          'returnByValue': True})
        return r.get('result', {}).get('result', {}).get('value')


def run(tag, url, selector, fname, attempt=0):
    profile = os.path.join(TMP, f'mec-ox2-sect-{tag}-{attempt}')
    shutil.rmtree(profile, ignore_errors=True)
    proc = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        '--remote-debugging-port=0', f'--user-data-dir={profile}', url,
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
        deadline = time.time() + 30
        while time.time() < deadline and not ws_url:
            try:
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
                pages = [t for t in tabs if t.get('type') == 'page' and t.get('webSocketDebuggerUrl')]
                if pages:
                    ws_url = pages[0]['webSocketDebuggerUrl']
            except Exception:
                pass
            time.sleep(0.4)
        if not ws_url:
            raise RuntimeError('no page tab')
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
        ws = WS(sock)
        ws.cmd('Page.enable'); ws.cmd('Runtime.enable')
        ws.cmd('Emulation.setDeviceMetricsOverride',
               {'width': 1440, 'height': 1050, 'deviceScaleFactor': 1, 'mobile': False})
        ok = None
        deadline = time.time() + 25
        while time.time() < deadline and not ok:
            ok = ws.js(f"(() => {{ const el = document.querySelector('{selector}');"
                       f" if (!el) return false; el.scrollIntoView({{block:'center'}}); return true; }})()")
            time.sleep(0.5)
        if not ok:
            raise RuntimeError('selector not found: ' + selector)
        time.sleep(2.5)
        try:
            ws.js('new Promise(r => setTimeout(r, 4500))', await_promise=True)
        except Exception:
            pass
        # re-scroll AFTER images/layout settled — late loads push sections down
        ws.js(f"document.querySelector('{selector}').scrollIntoView({{block:'center'}})")
        try:
            # 2.5s: enough for the slowest stagger child (delay .7s + duration .8s)
            ws.js('new Promise(r => setTimeout(r, 2500))', await_promise=True)
        except Exception:
            pass
        shot = ws.cmd('Page.captureScreenshot', {'format': 'png'})
        if 'result' not in shot:
            raise RuntimeError('capture failed: ' + json.dumps(shot.get('error', shot))[:200])
        with open(os.path.join(OUT, fname), 'wb') as fh:
            fh.write(base64.b64decode(shot['result']['data']))
        hidden = ws.js(f"Array.from(document.querySelectorAll('{selector} [data-reveal-child]'))"
                       ".filter(e=>parseFloat(getComputedStyle(e).opacity)<0.9).length")
        print(tag, '-> saved', fname, '| unrevealed children:', hidden)
        proc.kill()
        return True
    except Exception as e:
        print(tag, f'attempt {attempt} failed:', e)
        proc.kill()
        if attempt < 2:
            time.sleep(2)
            return run(tag, url, selector, fname, attempt + 1)
        return False


if __name__ == '__main__':
    def ensure_server():
        try:
            urllib.request.urlopen(BASE + '/index.html', timeout=2)
            print('server: already up')
            return None
        except Exception:
            pass
        srv = subprocess.Popen(
            ['python', '-m', 'http.server', '8123', '--bind', '127.0.0.1'],
            cwd=r'D:\work\merdian\ox 2', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            try:
                urllib.request.urlopen(BASE + '/index.html', timeout=2)
                print('server: started pid', srv.pid)
                return srv
            except Exception:
                time.sleep(0.5)
        raise RuntimeError('could not start local server')

    SRV = ensure_server()
    results = [run(*t) for t in TARGETS]
    print('ALL OK' if all(results) else 'SOME FAILED')
