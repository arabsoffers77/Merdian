#!/usr/bin/env python3
"""Verify: at the user's short viewport (1366x619), the Selected Work cards
must be FULLY VISIBLE after a real scroll to bottom (clampedStart fix)."""
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
        return r.get('result',{}).get('result',{}).get('value')


def connect(url):
    profile=os.path.join(TMP,'mec-ox2-short-%d'%(time.time()*1000%1e9))
    proc=subprocess.Popen([CHROME,'--headless=new','--disable-gpu','--no-sandbox',
      '--remote-debugging-port=0',f'--user-data-dir={profile}',url],
      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    port=None; dl=time.time()+30
    while time.time()<dl:
        f=os.path.join(profile,'DevToolsActivePort')
        if os.path.exists(f):
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
    return proc,ws


if __name__=='__main__':
    try:
        urllib.request.urlopen('http://127.0.0.1:8123/index.html',timeout=2); print('server up')
    except Exception:
        subprocess.Popen(['python','-m','http.server','8123','--bind','127.0.0.1'],
                         cwd=r'D:\work\merdian\ox 2',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    all_ok=True
    for w,h in [(1366,619),(1440,900),(1280,720)]:
        proc,ws=connect('http://127.0.0.1:8123/index.html')
        ws.cmd('Emulation.setDeviceMetricsOverride',
               {'width':w,'height':h,'deviceScaleFactor':1,'mobile':False})
        dl=time.time()+15
        while time.time()<dl:
            if ws.js("document.querySelectorAll('.chroma-card').length===6"): break
            time.sleep(0.4)
        # wait for images then refresh triggers like real browsing
        try: ws.js('new Promise(r=>setTimeout(r,2500))',True)
        except Exception: pass
        # scroll to bottom like a user
        ws.js("window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})")
        try: ws.js('new Promise(r=>setTimeout(r,2200))',True)
        except Exception: pass
        stinfo = ws.js("""(() => {
          const g=document.querySelector('.feat-grid');
          const st=ScrollTrigger.getAll().find(t=>t.trigger===g);
          return JSON.stringify({scrollY:Math.round(scrollY),
            maxScroll:Math.round(document.documentElement.scrollHeight-innerHeight),
            stStart:st?Math.round(st.start):null,
            stEnd:st?Math.round(st.end):null,
            stActive:st?st.isActive:null,
            stProgress:st?+(st.progress||0).toFixed(3):null,
            docReady:document.readyState});
        })()""")
        print('   state:', stinfo)
        res=json.loads(ws.js("""(() => {
          const g=document.querySelector('.feat-grid');
          const cells=[...g.querySelectorAll(':scope > [data-reveal-child]')];
          return JSON.stringify({vh:innerHeight,
            gridOp:getComputedStyle(g).opacity,
            cellOps:cells.map(c=>+getComputedStyle(c).opacity),
            visibleCells:cells.filter(c=>{
              const r=c.getBoundingClientRect();
              return r.top<innerHeight&&r.bottom>0&&+getComputedStyle(c).opacity===1}).length});
        })()"""))
        ok = res['gridOp']=='1' and all(o==1 for o in res['cellOps'])
        all_ok=all_ok and ok
        print(f"{w}x{h}: gridOp={res['gridOp']} cellsVisible={sum(1 for o in res['cellOps'] if o==1)}/6 -> {'PASS' if ok else 'FAIL'}")
        if w==1366:
            shot=ws.cmd('Page.captureScreenshot',{'format':'png'})
            open(os.path.join(OUT,'ox2-selected-work-fixed.png'),'wb').write(base64.b64decode(shot['result']['data']))
        proc.kill()
    print('SHORT-VIEWPORT REVEAL:', 'ALL PASS' if all_ok else 'FAIL')
