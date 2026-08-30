#!/usr/bin/env python3
"""Verify: hex orientation = logo (pointy-top, h/w 1.15), chroma spotlight
tracks pointer, cards never semi-transparent at rest."""
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
    profile=os.path.join(TMP,'mec-ox2-chroma-%d'%(time.time()*1000%1e9))
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

    proc,ws=connect('http://127.0.0.1:8123/index.html')
    ws.cmd('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1050,'deviceScaleFactor':1,'mobile':False})
    dl=time.time()+15
    while time.time()<dl:
        if ws.js("document.querySelectorAll('.hex').length===3"): break
        time.sleep(0.4)
    # hex aspect must be ~1.15 (pointy-top like the logo)
    hexok = json.loads(ws.js("""(() => {
      const h=document.querySelector('.hex-b'); const r=h.getBoundingClientRect();
      return JSON.stringify({ar:+(r.height/r.width).toFixed(3),
        clip:getComputedStyle(h).clipPath.indexOf('url')!==-1});
    })()"""))
    print('HEX:',hexok,'-> pointy-top OK' if abs(hexok['ar']-1.15)<0.02 else 'WRONG ASPECT')

    # chroma spotlight on Selected Work
    js_scroll = "document.querySelector('.feat-grid').scrollIntoView({block:'center',behavior:'instant'})"
    ws.js(js_scroll)
    try: ws.js('new Promise(r=>setTimeout(r,2600))',True)
    except Exception: pass
    cards=json.loads(ws.js("""(() => {
      const cs=[...document.querySelectorAll('.chroma-card')];
      return JSON.stringify({count:cs.length,
        restOps:cs.map(c=>+getComputedStyle(c).opacity),
        hasVeil:cs.every(c=>!!c.querySelector('.chroma-veil')),
        gridOp:getComputedStyle(document.querySelector('.feat-grid')).opacity});
    })()"""))
    print('CARDS:',cards)

    # dispatch real pointermove over first card and check --mx/--my update
    r=ws.js("(c=>{const b=c.getBoundingClientRect();return JSON.stringify({x:b.left+b.width/2,y:b.top+b.height/2})})(document.querySelector('.chroma-card'))")
    pos=json.loads(r)
    ws.js(f"""(() => {{
      const c=document.querySelector('.chroma-card');
      const b=c.getBoundingClientRect();
      const ev=new PointerEvent('pointermove',{{clientX:{int(pos['x'])},clientY:{int(pos['y'])},bubbles:true}});
      c.dispatchEvent(ev);
    }})()""")
    time.sleep(0.3)
    mx=ws.js("document.querySelector('.chroma-card').style.getPropertyValue('--mx')")
    my=ws.js("document.querySelector('.chroma-card').style.getPropertyValue('--my')")
    tracking = bool(mx and my and not mx.startswith('-'))
    print(f"SPOTLIGHT vars: --mx={mx} --my={my} -> {'PASS' if tracking else 'FAIL'}")

    shot=ws.cmd('Page.captureScreenshot',{'format':'png'})
    open(os.path.join(OUT,'ox2-chroma.png'),'wb').write(base64.b64decode(shot['result']['data']))
    # also capture hexes for visual orientation proof
    ws.js("document.querySelector('.hex-cluster').scrollIntoView({block:'center',behavior:'instant'})")
    time.sleep(1.0)
    shot=ws.cmd('Page.captureScreenshot',{'format':'png'})
    open(os.path.join(OUT,'ox2-hex-pointy.png'),'wb').write(base64.b64decode(shot['result']['data']))
    ok = abs(hexok['ar']-1.15)<0.02 and hexok['clip'] and all(o==1 for o in cards['restOps']) and cards['gridOp']=='1' and tracking
    print('CHROMA+HEX:', 'ALL PASS' if ok else 'FAIL')
    proc.kill()
