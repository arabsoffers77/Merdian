#!/usr/bin/env python3
"""Minimal repro: does a function-based start ever fire the tween?"""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'
profile=os.path.join(TMP,'mec-ox2-fnstart')
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
buf=b''; mid=[0]
def send(payload):
    data=payload.encode(); h=bytearray([0x81]); n=len(data); mask=os.urandom(4)
    if n<126: h.append(0x80|n)
    elif n<65536: h.append(0x80|126); h+=struct.pack('>H',n)
    else: h.append(0x80|127); h+=struct.pack('>Q',n)
    h+=mask
    s.sendall(bytes(h)+bytes(b^mask[i%4] for i,b in enumerate(data)))
def recvr():
    global buf
    while True:
        if len(buf)>=2:
            b1=buf[1]; ln=b1&0x7F; off=2
            if ln==126:
                if len(buf)<4: buf+=s.recv(65536); continue
                ln=struct.unpack('>H',buf[2:4])[0]; off=4
            elif ln==127:
                if len(buf)<10: buf+=s.recv(65536); continue
                ln=struct.unpack('>Q',buf[2:10])[0]; off=10
            if len(buf)>=off+ln:
                pl=buf[off:off+ln]; buf=buf[off+ln:]
                return json.loads(pl.decode('utf-8','replace'))
        c=s.recv(65536)
        if not c: raise RuntimeError('closed')
        buf+=c
def cmd(method,params=None):
    mid[0]+=1; myid=mid[0]
    send(json.dumps({'id':myid,'method':method,'params':params or {}}))
    while True:
        m=recvr()
        if m.get('id')==myid: return m
def js(expr,**kw):
    params={'expression':expr,'returnByValue':True}
    if kw.get('await'): params['awaitPromise']=True
    r=cmd('Runtime.evaluate',params)
    res=r.get('result',{}).get('result',{})
    exc=r.get('result',{}).get('exceptionDetails')
    if exc: return 'EXC:'+json.dumps(exc)[:200]
    return res.get('value')
cmd('Page.enable'); cmd('Runtime.enable')
time.sleep(2)
print('A: create fn-start trigger for feat-grid')
print(js("""(function(){
  const g=document.querySelector('.feat-grid');
  gsap.fromTo(g,{opacity:0},{opacity:1,duration:.4,
    scrollTrigger:{trigger:g,start:function(){return 100;},once:true}});
  ScrollTrigger.refresh();
  const st=ScrollTrigger.getAll().filter(function(t){return t.trigger===g});
  return JSON.stringify(st.map(function(t){return {start:t.start,isActive:t.isActive}}));
})()"""))
print('B: scroll to 300 and check opacity')
js("window.scrollTo({top:300,behavior:'instant'})")
try: js('new Promise(r=>setTimeout(r,1200))',True)
except Exception: pass
print(js("getComputedStyle(document.querySelector('.feat-grid')).opacity"))
proc.kill()
