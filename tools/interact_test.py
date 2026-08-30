#!/usr/bin/env python3
"""Interaction tests v2: per-test dynamic CDP port (DevToolsActivePort file),
readiness polling instead of blind sleeps. Covers rows, nav, filters (visual),
project modal, 3D flip cards, form validation."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

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

    def js(self, expr, await_promise=False):
        r = self.cmd('Runtime.evaluate', {'expression': expr, 'awaitPromise': await_promise,
                                          'returnByValue': True})
        res = r.get('result', {}).get('result', {})
        if 'exceptionDetails' in res or r.get('result', {}).get('exceptionDetails'):
            return None
        return res.get('value')

    def wait(self, expr, timeout=20):
        """Poll until js(expr) is truthy."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                v = self.js(expr)
                if v: return v
            except Exception:
                pass
            time.sleep(0.4)
        return None


def connect(target):
    import shutil
    profile = os.path.join(TMP, 'mec-ox2-it2-%d' % int(time.time() * 1000 % 1e9))
    shutil.rmtree(profile, ignore_errors=True)
    proc = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
        '--remote-debugging-port=0', f'--user-data-dir={profile}', target,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    port = None
    deadline = time.time() + 30
    while time.time() < deadline:
        f = os.path.join(profile, 'DevToolsActivePort')
        if os.path.exists(f):
            try:
                port = int(open(f).read().split('\n')[0].strip())
                break
            except Exception:
                pass
        time.sleep(0.3)
    if not port:
        proc.kill()
        raise RuntimeError('no DevToolsActivePort for ' + target)
    ws_url = None
    for _ in range(40):
        try:
            tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
            pages = [t for t in tabs if t.get('type') == 'page']
            if pages:
                ws_url = pages[0]['webSocketDebuggerUrl']
                break
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
    while b'\r\n\r\n' not in resp:
        resp += sock.recv(4096)
    ws = WS(sock)
    ws.cmd('Page.enable'); ws.cmd('Runtime.enable')
    return proc, ws


def test_expand_rows():
    proc, ws = connect(BASE + '/services.html')
    ok_page = ws.wait("document.querySelectorAll('.xrow').length === 8")
    before = float(ws.js("document.querySelector('#design .xrow-panel').getBoundingClientRect().height"))
    ws.js("document.querySelector('#design .xrow-btn').click()")
    time.sleep(0.6)
    after = float(ws.js("document.querySelector('#design .xrow-panel').getBoundingClientRect().height"))
    expanded = ws.js("document.querySelector('#design .xrow-btn').getAttribute('aria-expanded')")
    print(f"EXPAND ROWS: {before}px -> {after}px, expanded={expanded}",
          "PASS" if ok_page and after > 40 and expanded == 'true' else "FAIL")
    proc.kill()


def test_mobile_nav():
    proc, ws = connect(BASE + '/index.html')
    ok_page = ws.wait("document.querySelectorAll('.main-nav a.nav-link').length === 6")
    ws.cmd('Emulation.setDeviceMetricsOverride',
           {'width': 390, 'height': 844, 'deviceScaleFactor': 2, 'mobile': True})
    time.sleep(0.5)
    ws.js("document.querySelector('.nav-toggle').click()")
    time.sleep(0.6)
    open_h = float(ws.js("document.querySelector('.main-nav').getBoundingClientRect().height"))
    links = int(ws.js("document.querySelectorAll('.main-nav a.nav-link').length"))
    print(f"MOBILE NAV: open {open_h}px, links={links}",
          "PASS" if ok_page and open_h > 200 and links == 6 else "FAIL")
    proc.kill()


def test_filters():
    proc, ws = connect(BASE + '/projects.html')
    ok_page = ws.wait("document.querySelectorAll('[data-category]').length === 6")
    all_vis = int(ws.js("Array.from(document.querySelectorAll('[data-category]')).filter(c=>c.offsetParent!==null).length"))
    ws.js("document.querySelector('.chip[data-filter=\"hospitality\"]').click()")
    time.sleep(0.6)
    hosp_vis = int(ws.js("Array.from(document.querySelectorAll('[data-category]')).filter(c=>c.offsetParent!==null).length"))
    active_ok = bool(ws.js("document.querySelector('.chip[data-filter=\"hospitality\"]').classList.contains('is-active')"))
    print(f"FILTERS: allVisible={all_vis}, hospitalityVisible={hosp_vis}, chipActive={active_ok}",
          "PASS" if ok_page and all_vis == 6 and hosp_vis == 4 and active_ok else "FAIL")
    proc.kill()


def test_modal():
    proc, ws = connect(BASE + '/projects.html')
    ok_page = ws.wait("!!document.getElementById('proj-salalah')")
    ws.js("document.getElementById('proj-salalah').click()")
    time.sleep(0.5)
    open_state = ws.js("document.getElementById('project-modal').getAttribute('aria-hidden')")
    name = ws.js("document.getElementById('pm-name').textContent") or ''
    desc_len = len(ws.js("document.getElementById('pm-desc').textContent") or '')
    img_ok = bool(ws.js("(document.getElementById('pm-img').src||'').indexOf('proj-salalah') !== -1"))
    locked = ws.js("document.body.style.overflow") or ''
    ws.js("document.querySelector('.pmodal-close').click()")
    time.sleep(0.4)
    closed = ws.js("document.getElementById('project-modal').getAttribute('aria-hidden')")
    unlocked = bool(ws.js("document.body.style.overflow === ''"))
    ok = (ok_page and open_state == 'false' and name == 'Grand Salalah Resort' and desc_len > 80
          and img_ok and locked == 'hidden' and closed == 'true' and unlocked)
    print(f"MODAL: open={open_state}, name={name!r}, descLen={desc_len}, imgOk={img_ok}, "
          f"locked={locked!r}, closed={closed}, unlocked={unlocked}", "PASS" if ok else "FAIL")
    proc.kill()


def test_flip():
    proc, ws = connect(BASE + '/about.html')
    ok_page = ws.wait("document.querySelectorAll('.flip-card').length === 5")
    n = int(ws.js("document.querySelectorAll('.flip-card').length"))
    pressed0 = ws.js("document.querySelector('.flip-card').getAttribute('aria-pressed')")
    ws.js("document.querySelector('.flip-card').click()")
    time.sleep(0.4)
    cls = bool(ws.js("document.querySelector('.flip-card').classList.contains('is-flipped')"))
    pressed1 = ws.js("document.querySelector('.flip-card').getAttribute('aria-pressed')")
    ws.js("document.querySelector('.flip-card').dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', bubbles:true}))")
    time.sleep(0.3)
    cls2 = bool(ws.js("document.querySelector('.flip-card').classList.contains('is-flipped')"))
    backface = ws.js("getComputedStyle(document.querySelector('.flip-card .flip-face--back')).backfaceVisibility")
    unflipped_by_enter = not cls2
    ok = ok_page and n == 5 and pressed0 == 'false' and cls and pressed1 == 'true' and unflipped_by_enter
    print(f"FLIP: cards={n}, pressed {pressed0}->{pressed1}, clickFlip={cls}, enterUnflips={unflipped_by_enter}, "
          f"backface={backface}", "PASS" if ok else "FAIL")
    proc.kill()


def test_form():
    proc, ws = connect(BASE + '/contact.html')
    ok_page = ws.wait("!!document.getElementById('contact-form')")
    ws.js("document.querySelector('#contact-form button[type=submit]').click()")
    time.sleep(0.5)
    errors = int(ws.js("document.querySelectorAll('.field.has-error').length"))
    shown0 = bool(ws.js("document.getElementById('form-success').classList.contains('is-visible')"))
    ws.js("document.getElementById('cf-name').value='Test User';"
          "document.getElementById('cf-email').value='test@example.com';"
          "document.getElementById('cf-message').value='A test message.';"
          "document.querySelector('#contact-form button[type=submit]').click()")
    time.sleep(0.6)
    shown1 = bool(ws.js("document.getElementById('form-success').classList.contains('is-visible')"))
    ok = ok_page and errors == 3 and not shown0 and shown1
    print(f"FORM: emptyErrors={errors}, successBefore={shown0}, successAfterFill={shown1}",
          "PASS" if ok else "FAIL")
    proc.kill()


if __name__ == '__main__':
    import shutil, glob

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
    for d in glob.glob(os.path.join(TMP, 'mec-ox2-interact*')) + glob.glob(os.path.join(TMP, 'mec-ox2-it2-*')):
        shutil.rmtree(d, ignore_errors=True)
    test_expand_rows()
    test_mobile_nav()
    test_filters()
    test_modal()
    test_flip()
    test_form()
