import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'_media_work/range-reviews.json').read_text(encoding='utf8'))
for offset in range(0,len(rows),7):
    batch=rows[offset:offset+7]
    canvas=Image.new('RGB',(1500,len(batch)*310),'#eeeeee')
    draw=ImageDraw.Draw(canvas)
    for i,row in enumerate(batch):
        streams=row['metadata']['streams']
        v=next(s for s in streams if s['codec_type']=='video')
        label=row['path'].replace('Client/','')+f"  {v['width']}x{v['height']} / {float(row['metadata']['format']['duration']):.2f}s"
        draw.text((8,i*310+8),label,fill='black')
        for j,frame in enumerate(row['frames']):
            with Image.open(ROOT/frame['file']) as im:
                canvas.paste(ImageOps.contain(im.convert('RGB'),(490,270)),(j*500+5,i*310+32))
    canvas.save(ROOT/f'_media_work/video-comparison-{offset//7+1}.jpg',quality=92)
