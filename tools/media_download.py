"""Download selected public client files to the backup's excluded working cache."""
import concurrent.futures as cf
import html
import http.cookiejar
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '_media_work'

def download(item):
    dest = WORK / 'originals' / (item['id'] + Path(item['name']).suffix.lower())
    dest.parent.mkdir(exist_ok=True)
    size = re.search(r'([\d,.]+)\s*(KB|MB|GB)',item.get('size') or '')
    minimum = float(size.group(1).replace(',','.')) * {'KB':1000,'MB':1000000,'GB':1000000000}[size.group(2)] * .95 if size else 10000
    verified=dest.with_suffix(dest.suffix+'.verified.json')
    if dest.exists() and verified.exists():
        record=json.loads(verified.read_text(encoding='utf8'))
        if record['sha256']==hashlib.sha256(dest.read_bytes()).hexdigest():return dest
    temp = dest.with_suffix(dest.suffix+'.part')
    headers=temp.with_suffix(temp.suffix+'.headers')
    url = 'https://drive.usercontent.google.com/download?' + urllib.parse.urlencode({'id':item['id'],'export':'download','confirm':'t'})
    # Fresh transfers prevent a resumed request from combining incompatible bytes.
    subprocess.run(['curl.exe','-L','--fail','--retry','3','--retry-all-errors','--connect-timeout','20','--max-time','180','--speed-time','25','--speed-limit','1024','-sS','-D',str(headers),url,'-o',str(temp)],check=True)
    lengths=re.findall(r'content-length:\s*(\d+)',headers.read_text(encoding='utf8',errors='replace'),re.I)
    if lengths and temp.stat().st_size!=int(lengths[-1]):raise RuntimeError('Content-Length does not match downloaded file')
    if temp.stat().st_size < minimum:
        raise RuntimeError('Incomplete download: '+str(temp.stat().st_size)+' bytes')
    temp.replace(dest)
    verified.write_text(json.dumps({'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size}),encoding='utf8')
    return dest

def probe_video(item, remote=False):
    path = ('https://drive.usercontent.google.com/download?' + urllib.parse.urlencode({'id':item['id'],'export':'download','confirm':'t'})) if remote else download(item)
    network = ['-rw_timeout','15000000'] if remote else []
    data = json.loads(subprocess.check_output(['ffprobe','-v','error',*network,'-show_format','-show_streams','-of','json',str(path)],timeout=75))
    result = dict(item, metadata=data, review='remote frame samples' if remote else 'downloaded original')
    duration = float(data['format']['duration'])
    out = WORK/'video-frames'/item['id']
    out.mkdir(parents=True,exist_ok=True)
    for n,fraction in enumerate((.18,.5,.82) if remote else (.08,.22,.38,.55,.72,.88)):
        frame = out/f'{n+1}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y',*network,'-ss',str(duration*fraction),'-i',str(path),'-frames:v','1','-vf','scale=640:-2,format=yuvj420p',str(frame)],check=True,timeout=75)
    print('VIDEO',item['path'],duration,'seconds',data['format'].get('size'),flush=True)
    return result

if __name__ == '__main__':
    items = json.loads((WORK/'inventory.json').read_text(encoding='utf8'))
    if '--videos' in sys.argv or '--remote-videos' in sys.argv:
        selected = [r for r in items if r['name'].lower().endswith(('.mp4','.mov'))]
        results=[]
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(probe_video,r,'--remote-videos' in sys.argv):r for r in selected}
            for future in cf.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append(dict(futures[future], error=str(exc)))
                    print('VIDEO ERROR',futures[future]['path'],str(exc),flush=True)
                (WORK/'videos.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
    else:
        ids=set(sys.argv[1:])
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(download,r):r for r in items if r['id'] in ids}
            for future in cf.as_completed(futures):
                try:
                    print(futures[future]['path'], future.result(),flush=True)
                except Exception as exc:
                    print('DOWNLOAD ERROR',futures[future]['path'],str(exc),flush=True)
