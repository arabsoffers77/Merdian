"""Create responsive WebP copies from the reviewed client originals.
Originals stay in _media_work (excluded from upload). Re-run after downloading
the exact Drive files listed in media_selections.json. No network calls here.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'_media_work'
OUT=ROOT/'assets/media'
OUT.mkdir(exist_ok=True)

def source(selection):
    if selection.get('frame'):
        return Image.open(ROOT/selection['frame'])
    path=WORK/'originals'/(selection['id']+selection['extension'])
    if selection['extension']=='.pdf':
        pdf=PdfReader(path)
        image=pdf.pages[selection['pdf_page']-1].images[selection.get('pdf_image',0)]
        from io import BytesIO
        return Image.open(BytesIO(image.data))
    return Image.open(path)

def prepare(selection):
    with source(selection) as raw:
        im=ImageOps.exif_transpose(raw).convert('RGB')
        variants=[]
        widths=sorted(set(min(w,im.width) for w in (480,800,1200,1600,1920)))
        for width in widths:
            height=round(im.height*width/im.width)
            copy=im.resize((width,height),Image.Resampling.LANCZOS)
            dest=OUT/f"{selection['key']}-{width}.webp"
            copy.save(dest,'WEBP',quality=83,method=6)
            variants.append(dict(src=dest.relative_to(ROOT).as_posix(),width=width,height=height,bytes=dest.stat().st_size))
        row=dict(selection,width=im.width,height=im.height,variants=variants)
        row['fit']='contain' if im.width/im.height<1.0 else 'cover'
        print(selection['key'],im.size,variants[-1]['bytes'],flush=True)
        return row

def main():
    selections=json.loads((ROOT/'tools/media_selections.json').read_text(encoding='utf8'))
    rows=[]
    missing=[]
    for item in selections['projects']:
        try:
            rows.append(prepare(item))
        except FileNotFoundError:
            missing.append(item['key'])
    logo=Image.open(ROOT/'assets/img/logo.png').convert('RGBA')
    logo.thumbnail((180,180),Image.Resampling.LANCZOS)
    logo.save(OUT/'logo.png',optimize=True)
    result=dict(projects=rows,featured=selections['featured'],video=selections.get('video',{}),
                missing=missing,source='Client-supplied Google Drive project library',
                note='Names follow client folders. Visualization does not establish construction status or contract scope.')
    (OUT/'catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('Prepared',len(rows),'projects. Missing:',missing)
    if not missing:
        from photo_grade import main as prepare_grade
        prepare_grade()

if __name__=='__main__':
    main()
