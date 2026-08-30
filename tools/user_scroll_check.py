#!/usr/bin/env python3
"""Full-page user-scroll simulation at 1366x619: step through like a real
user, verify EVERY data-reveal lights up (incl. feat-grid), then screenshot."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'
OUT = r'D:\work\merdian\ox 2\_verify'


class WS:
    def __init__(self, sock):
        self.sock=sock; self.buf=b''; self.mid=0
    def send(self,payload):
        data=payload.encode(); h=bytearray([0x81]); n=len(data); mask=os.urandom(4)
        if n<126: h.append(0x80|n)
        elif n<65536: h.append(0x80|126); h+=struct.pack('>H',n)
        else: h.append(0x80|127); h+=struct.pack('>Q',n)
        h+=mask
        self.sock.sendall(bytes(h)+bytes(b^mask[i%4] for i,b in enumerate(data)))
    def recv_raw(self):
        while True:
            if len(self.buf)>=2:
                b1=self.buf[1]; ln=b1&0x7F; off=2
                if ln==126:
                    if len(self.buf)<4: self.buf+=self.sock.recv(65536); continue
                    ln=struct.unpack('>H',self.buf[2:4])[0]; off=4
                elif ln==127:
                    if len(self.buf)<10: self.buf+=self.sock.recv(65536); continue
                    ln=struct.unpack('>Q',self.buf[2:10])[0]; off=10
                if len(self.buf)>=off+ln:
                    pl=self.buf[off:off+ln]; self.buf=self.buf[off+ln:]
                    return json.loads(pl.decode('utf-8','replace'))
            c=self.sock.recv(65536)
            if not c: raise RuntimeError('closed')
            self.buf+=c
    def cmd(self,method,params=None):
        self.mid+=1; myid=self.mid
        self.send(json.dumps({'id':myid,'method':method,'params':params or {}}))
        while True:
            m=self.recv_raw()
            if m.get('id')==myid: return m
    def js(self,expr,**kw):
        params={'expression':expr,'returnByValue':True}
        if kw.get('await'): params['awaitPromise']=True
        r=self.cmd('Runtime.evaluate',params)
        res=r.get('result',{}).get('result',{})
        exc=r.get('result',{}).get('exceptionDetails')
        if exc: return 'EXC:'+json.dumps(exc)[:200]
        return res.get('value')


if __name__=='__main__':
    try:
        urllib.request.urlopen('http://127.0.0.1:8123/index.html',timeout=2); print('server up')
    except Exception:
        subprocess.Popen(['python','-m','http.server','8123','--bind','127.0.0.1'],
                         cwd=r'D:\work\merdian\ox 2',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    proc=subprocess.Popen([CHROME,'--headless=new','--disable-gpu','--no-sandbox',
      '--remote-debugging-port=0','--user-data-dir='+os.path.join(TMP,'mec-ox2-user%d'%(time.time()*1000%1e9)),'http://127.0.0.1:8123/index.html'],
      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    import glob as _g
    port=None; dl=time.time()+30
    while time.time()<dl:
        f=None
        cands=_g.glob(os.path.join(TMP,'mec-ox2-user*','DevToolsActivePort'))
        if cands: f=cands[0]
        if f and os.path.exists(f):
            try: port=int(open(f).read().split('\n')[0].strip()); break
            except Exception: pass
        time.sleep(0.3)
    ws_url=None
    for _ in range(40):
        try:
            tabs=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
            pages=[t for t in tabs if t.get('type')=='page']
            if pages: ws_url=pages[0]['webSocketDebuggerUrl']; break
        except Exception: pass
        time.sleep(0.4)
    p=urllib.parse.urlparse(ws_url)
    s=socket.create_connection((p.hostname,p.port))
    key=base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET {p.path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    resp=b''
    while b'\r\n\r\n' not in resp: resp+=s.recv(4096)
    ws=WS(s); ws.cmd('Page.enable'); ws.cmd('Runtime.enable')
    ws.cmd('Emulation.setDeviceMetricsOverride',
           {'width':1366,'height':619,'deviceScaleFactor':1,'mobile':False})
    dl=time.time()+15
    while time.time()<dl:
        if ws.js("document.querySelectorAll('.chroma-card').length===6"): break
        time.sleep(0.4)
    # slow user-like stepping to the very bottom (wheel events = real scroll)
    for i in range(14):
        ws.cmd('Input.dispatchMouseEvent',
               {'type': 'mouseWheel', 'x': 700, 'y': 300, 'deltaX': 0, 'deltaY': 420})
        try: ws.js('new Promise(r=>setTimeout(r,450))',True)
        except Exception: pass
    res=json.loads(ws.js("""(() => {
      const g=document.querySelector('.feat-grid');
      const cells=[...g.querySelectorAll(':scope > [data-reveal-child]')];
      return JSON.stringify({y:Math.round(scrollY),
        gridCls:g.className,
        gridOp:getComputedStyle(g).opacity,
        cellOps:cells.map(c=>+getComputedStyle(c).opacity),
        totalIn:document.querySelectorAll('.is-in').length});
    })()"""))
    print(res)
    ok = res['gridOp']=='1' and all(o>=0.99 for o in res['cellOps'])
    print('USER-SCROLL REVEAL:', 'PASS' if ok else 'FAIL')
    shot=ws.cmd('Page.captureScreenshot',{'format':'png'})
    open(os.path.join(OUT,'ox2-selected-work-fixed.png'),'wb').write(base64.b64decode(shot['result']['data']))
    print('saved screenshot')
    proc.kill()
