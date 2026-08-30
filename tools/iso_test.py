#!/usr/bin/env python3
"""THE decisive isolation: on the LIVE site, create a fresh trigger with the
same clampedStart fn on cta-band (which has NO site tween), scroll past,
does it fire? This isolates site-tween interference from fn-start behavior."""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'


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


if __name__=='__main__':
    try:
        urllib.request.urlopen('http://127.0.0.1:8123/index.html',timeout=2)
    except Exception:
        subprocess.Popen(['python','-m','http.server','8123','--bind','127.0.0.1'],
                         cwd=r'D:\work\merdian\ox 2',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    profile=os.path.join(TMP,'mec-ox2-iso')
    proc=subprocess.Popen([CHROME,'--headless=new','--disable-gpu','--no-sandbox',
      '--remote-debugging-port=0',f'--user-data-dir={profile}','http://127.0.0.1:8123/index.html'],
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
    time.sleep(2)

    # 1) fresh ST with fn start on .cta-band — fire?
    ws.js("""(function(){
      window.__fired=false;
      const band=document.querySelector('.cta-band');
      ScrollTrigger.create({trigger:band,
        start:function(){var t=band.getBoundingClientRect().top+(window.pageYOffset||0);
          return Math.max(0,Math.min(t-window.innerHeight*0.86,ScrollTrigger.maxScroll(window)-2));},
        once:true,onEnter:function(){window.__fired=true;}});
    })()""")
    ws.js("window.scrollTo({top:999999,behavior:'instant'})")
    try: ws.js('new Promise(r=>setTimeout(r,1500))',True)
    except Exception: pass
    print('fresh fn-start trigger fired:', ws.js("window.__fired"))

    # 2) NOW hijack the LIVE feat-grid trigger's start to a plain string and see if IT fires
    ws.js("""(function(){
      window.__gridFired=false;
      const g=document.querySelector('.feat-grid');
      const st=ScrollTrigger.getAll().find(function(t){return t.trigger===g});
      st.vars.onEnter=function(){window.__gridFired=true;};
      st.start='top 80%';
      st.end='bottom 20%';
      st.refresh();
    })()""")
    ws.js("window.scrollTo({top:0,behavior:'instant'})")
    time.sleep(0.4)
    ws.js("window.scrollTo({top:999999,behavior:'instant'})")
    try: ws.js('new Promise(r=>setTimeout(r,1800))',True)
    except Exception: pass
    print('live trigger with STRING start fired:', ws.js("window.__gridFired"),
          '| grid class:', ws.js("document.querySelector('.feat-grid').className"))
    proc.kill()
