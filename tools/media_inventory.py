"""Read the client's public Drive folder. Local cache only; never writes to Drive."""
import concurrent.futures as cf
import html
import json
from pathlib import Path
import re
import urllib.request
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '_media_work'
WORK.mkdir(exist_ok=True)
FOLDER = '1_LtkWsczaHQdlpLOwGpnn4Dfy1tn8zW2'

def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=65) as response:
        return response.read()

def folder(item):
    ident, path = item
    cache = WORK / (ident + '.html')
    if not cache.exists():
        cache.write_bytes(get('https://drive.google.com/drive/folders/' + ident))
    source = cache.read_text(encoding='utf8')
    result = []
    for row in re.findall(r'<tr\b[^>]*data-id=.*?</tr>', source, re.S):
        fid = re.search(r'data-id="([^"]+)"', row).group(1)
        name = re.search(r'<strong[^>]*>(.*?)</strong>', row, re.S)
        if not name:
            continue
        name = html.unescape(re.sub('<[^>]+>', '', name.group(1)))
        isfolder = bool(re.search(r'aria-label="[^"]*(?:Shared folder|Folder)"', row, re.I))
        size = re.search(r'aria-label="(?:Size: |Size )?([0-9.,]+\s*(?:KB|MB|GB|bytes))"', row, re.I)
        if not size:
            size = re.search(r'>([0-9.,]+\s*(?:KB|MB|GB))<', row)
        result.append(dict(id=fid, name=name, path=path + '/' + name,
                           folder=isfolder, size=size.group(1) if size else None))
    return result

def inventory():
    allitems, queue, seen = [], [(FOLDER, 'Client')], set()
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        while queue:
            batch = [i for i in queue if i[0] not in seen]
            queue = []
            seen.update(i[0] for i in batch)
            for item, future in zip(batch, [pool.submit(folder, i) for i in batch]):
                try:
                    rows = future.result()
                    print(item[1], len(rows), flush=True)
                    allitems.extend(rows)
                    queue.extend((r['id'], r['path']) for r in rows if r['folder'])
                except Exception as exc:
                    print('ERROR', item, str(exc), flush=True)
    (WORK / 'inventory.json').write_text(json.dumps(allitems, ensure_ascii=False, indent=2), encoding='utf8')
    return allitems

def thumbnail(item):
    dest = WORK / 'thumbs' / (item['id'] + '.jpg')
    dest.parent.mkdir(exist_ok=True)
    if not dest.exists():
        dest.write_bytes(get('https://drive.google.com/thumbnail?id=' + item['id'] + '&sz=w800'))
    with Image.open(dest) as image:
        image.verify()
    return dest

def sheets(items, available=False):
    pictures = [r for r in items if not r['folder'] and r['name'].lower().endswith(('.jpg','.jpeg','.png','.pdf','.mp4','.mov'))]
    if available:
        pictures = [r for r in pictures if (WORK/'thumbs'/(r['id']+'.jpg')).exists()]
    groups = {}
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for r, future in zip(pictures, [pool.submit(thumbnail, r) for r in pictures]):
            try:
                r['thumbnail'] = str(future.result().relative_to(ROOT))
                groups.setdefault(r['path'].rsplit('/',1)[0], []).append(r)
            except Exception as exc:
                r['thumbnail_error'] = str(exc)
                print('THUMB ERROR', r['path'], str(exc), flush=True)
    catalog = []
    out = WORK / ('available-sheets' if available else 'sheets')
    out.mkdir(exist_ok=True)
    for number, (group, rows) in enumerate(groups.items(), 1):
        for page in range(0,len(rows),20):
            subset = rows[page:page+20]
            canvas = Image.new('RGB', (1400, 50+245*((len(subset)+3)//4)), '#eeeeee')
            draw = ImageDraw.Draw(canvas)
            draw.text((12,12),group, fill='black')
            for n,r in enumerate(subset):
                x,y = (n%4)*350,50+(n//4)*245
                with Image.open(ROOT / r['thumbnail']) as im:
                    fit = ImageOps.contain(im.convert('RGB'),(340,198))
                    canvas.paste(fit,(x+(350-fit.width)//2,y))
                draw.text((x+6,y+200),str(page+n+1)+'. '+r['name'][:44],fill='black')
                draw.text((x+6,y+217),r['id'],fill='#555555')
            name = f'{number:02d}-{page//20+1}.jpg'
            canvas.save(out/name,quality=90)
            catalog.append(dict(group=group,file=name,items=subset))
    if not available:
        (WORK/'inventory.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf8')
    (WORK/('available-sheets.json' if available else 'sheets.json')).write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')
    print('SHEETS', len(catalog), 'MEDIA',len(pictures),flush=True)

if __name__ == '__main__':
    import sys
    if '--sheets' in sys.argv:
        sheets(json.loads((WORK/'inventory.json').read_text(encoding='utf8')), '--available' in sys.argv)
    else:
        inventory()
