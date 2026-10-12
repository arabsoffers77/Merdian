"""Review public Drive video samples without downloading multi-GB originals.
Only validated byte ranges are cached. These incomplete source caches are NOT
deliverables. Any exported film must pass a complete decode check.
"""
import concurrent.futures as cf
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'_media_work'
CACHE=WORK/'video-range-cache'
CACHE.mkdir(exist_ok=True)

def url(item):
    return 'https://drive.usercontent.google.com/download?'+urllib.parse.urlencode({'id':item['id'],'export':'download','confirm':'t'})

def byte_range(item,start,end):
    dest=CACHE/f"{item['id']}-{start}-{end}.bin"
    head=dest.with_suffix('.headers')
    if not dest.exists() or dest.stat().st_size!=end-start+1:
        for attempt in range(3):
            result=subprocess.run(['curl.exe','--http1.1','-L','--fail','--connect-timeout','12','--max-time','35','--range',f'{start}-{end}','-sS','-D',str(head),url(item),'-o',str(dest)],capture_output=True)
            if result.returncode==0 and dest.exists() and dest.stat().st_size==end-start+1:
                break
        else:
            raise RuntimeError('Could not retrieve range '+str((start,end)))
    headers=head.read_text(encoding='utf8',errors='replace')
    match=re.search(r'content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)',headers,re.I)
    if not match or int(match[1])!=start or int(match[2])!=end:
        raise RuntimeError('Invalid Content-Range')
    return dest,int(match[3])

def insert(cache,part,start):
    with cache.open('r+b') as output:
        output.seek(start)
        output.write(part.read_bytes())

def prepare(item):
    original=WORK/'originals'/(item['id']+Path(item['name']).suffix)
    size=re.search(r'([\d,.]+)\s*MB',item.get('size') or '')
    if original.exists() and size and original.stat().st_size>float(size[1].replace(',','.'))*950000:
        data=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(original)],timeout=20))
        return original,data
    first,total=byte_range(item,0,1048575)
    cache=CACHE/(item['id']+Path(item['name']).suffix)
    if not cache.exists():
        with cache.open('wb') as output:
            output.truncate(total)
    insert(cache,first,0)
    laststart=max(1048576,total-2097152)
    last,_=byte_range(item,laststart,total-1)
    insert(cache,last,laststart)
    data=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(cache)],timeout=20))
    return cache,data

def packets(cache,start,seconds):
    result=subprocess.run(['ffprobe','-v','quiet','-select_streams','v:0','-read_intervals',f'{start}%+{seconds}','-show_packets','-show_entries','packet=pts_time,pos,size,flags','-of','json',str(cache)],capture_output=True,timeout=30)
    return json.loads(result.stdout).get('packets',[])

def fetch_interval(item,cache,start,seconds):
    entries=packets(cache,start,seconds)
    if not entries:
        raise RuntimeError('No indexed packets')
    low=min(int(x['pos']) for x in entries)
    high=max(int(x['pos'])+int(x['size']) for x in entries)-1
    for offset in range(low,high+1,1048576):
        end=min(high,offset+1048575)
        part,_=byte_range(item,offset,end)
        insert(cache,part,offset)
    return low,high

def review(item):
    cache,data=prepare(item)
    duration=float(data['format']['duration'])
    out=WORK/'video-frames'/item['id']
    out.mkdir(parents=True,exist_ok=True)
    frames=[]
    for n,fraction in enumerate((.18,.50,.82),1):
        t=duration*fraction
        frame=out/f'range-{n}.png'
        if frame.exists():
            frames.append(dict(file=str(frame.relative_to(ROOT)),time=t))
            continue
        entries=packets(cache,t,1)
        keys=[x for x in entries if 'K' in x.get('flags','')]
        # Seeking the MP4 sample table starts at its preceding sync sample.
        # An uncached NAL payload cannot yet be marked K by ffprobe's parser.
        key=keys[0] if keys else entries[0]
        if cache.parent==CACHE:
            fetch_interval(item,cache,t,.20)
        subprocess.run(['ffmpeg','-v','error','-y','-ss',key['pts_time'],'-i',str(cache),'-map','0:v:0','-frames:v','1','-an','-vf','scale=640:-2',str(frame)],capture_output=True,timeout=30)
        if not frame.exists():
            raise RuntimeError('Frame decode produced no image')
        frames.append(dict(file=str(frame.relative_to(ROOT)),time=float(key['pts_time'])))
    return dict(item,metadata=data,frames=frames,review='three indexed frame samples',cache=str(cache.relative_to(ROOT)))

if __name__=='__main__':
    items=json.loads((WORK/'inventory.json').read_text(encoding='utf8'))
    items=[r for r in items if r['name'].lower().endswith(('.mp4','.mov'))]
    if len(sys.argv)>1:
        items=[r for r in items if r['id'] in sys.argv[1:]]
    previous=WORK/'range-reviews.json'
    results={r['id']:r for r in json.loads(previous.read_text(encoding='utf8'))} if previous.exists() else {}
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(review,r):r for r in items}
        for f in cf.as_completed(futures):
            try:
                row=f.result()
                print('REVIEWED',row['path'],flush=True)
            except Exception as exc:
                row=dict(futures[f],error=str(exc))
                print('REVIEW ERROR',row['path'],str(exc),flush=True)
            results[row['id']]=row
            (WORK/'range-reviews.json').write_text(json.dumps(list(results.values()),ensure_ascii=False,indent=2),encoding='utf8')
