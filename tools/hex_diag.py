#!/usr/bin/env python3
"""Diagnose hex clip: is the SVG clipPath present, applied, and does the
rendered silhouette actually have rounded corners (pixel-scan the corners)?"""
import base64, json, os, socket, struct, subprocess, time, urllib.request, urllib.parse

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
TMP = r'C:\Users\ASUS\AppData\Local\Temp'

proc = subprocess.Popen([CHROME,'--headless=new','--disable-gpu','--no-sandbox',
  '--remote-debugging-port=0',f'--user-data-dir={TMP}\\mec-ox2-hexdiag','http://127.0.0.1:8123/index.html'],
  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
port=None; dl=time.time()+30
while time.time()<dl:
    f=os.path.join(TMP,'mec-ox2-hexdiag','DevToolsActivePort')
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
def js(expr):
    r=cmd('Runtime.evaluate',{'expression':expr,'returnByValue':True})
    return r.get('result',{}).get('result',{}).get('value')
cmd('Page.enable'); cmd('Runtime.enable')
out={}
out['clipInDom'] = js("!!document.getElementById('mecHexClip')")
out['pathD'] = js("document.getElementById('mecHexClip')?.getAttribute('d')")[:60]
out['applied'] = js("getComputedStyle(document.querySelector('.hex')).clipPath")
# geometric probe: sample points near a corner to see where opacity ends.
# A rounded corner leaves the extreme tip TRANSPARENT; sharp fills it.
probe = js("""(() => {
  const h = document.querySelector('.hex-b');
  const img = h.querySelector('.hex-img');
  const r = h.getBoundingClientRect();
  // right vertex tip of the hexagon (mid height, far right)
  const cx = Math.round(r.right) - 3;
  const cy = Math.round(r.top + r.height / 2);
  return fetch ? 'skip' : '';
})()""")
print(json.dumps(out, indent=1)[:400])
proc.kill()
