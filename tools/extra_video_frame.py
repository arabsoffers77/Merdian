"""Read one additional indexed frame from a reviewed client video."""
import json
from pathlib import Path
import subprocess
import sys
from review_video_ranges import prepare,packets,fetch_interval
ROOT=Path(__file__).resolve().parents[1]
ident=sys.argv[1]
t=float(sys.argv[2])
item=next(r for r in json.loads((ROOT/'_media_work/inventory.json').read_text(encoding='utf8')) if r['id']==ident)
cache,data=prepare(item)
entries=packets(cache,t,.2)
fetch_interval(item,cache,t,.2)
out=ROOT/f'_media_work/video-frames/{ident}/extra-{int(t)}.png'
subprocess.run(['ffmpeg','-v','quiet','-y','-ss',entries[0]['pts_time'],'-i',str(cache),'-map','0:v:0','-an','-frames:v','1',str(out)],timeout=30)
assert out.exists()
print(out)
