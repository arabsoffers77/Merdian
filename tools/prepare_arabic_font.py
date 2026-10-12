"""Self-host Noto Sans Arabic from official Google Fonts."""
from pathlib import Path
import re
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/fonts'

def read(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
    with urllib.request.urlopen(request,timeout=30) as response:return response.read()

def main():
    OUT.mkdir(exist_ok=True)
    url='https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400..800&display=swap'
    css=read(url).decode('utf8')
    (ROOT/'_media_work/arabic-font-source.css').write_text(css,encoding='utf8')
    parts=[]
    for subset,block in re.findall(r'/\*\s*([^*]+?)\s*\*/\s*(@font-face\s*\{[^}]+\})',css):
        if subset.strip() not in ('arabic','latin','latin-ext'):continue
        remote=re.search(r'url\((https:[^)]+)\)',block)[1]
        name=f'noto-sans-arabic-variable-{subset.strip()}.woff2'
        data=read(remote)
        assert data[:4]==b'wOF2','Expected a valid WOFF2 font'
        (OUT/name).write_bytes(data)
        parts.append(block.replace(remote,name))
        print(name,len(data),flush=True)
    assert parts,'No font faces returned'
    (OUT/'noto-sans-arabic.css').write_text('\n'.join(parts),encoding='utf8')
    (OUT/'OFL-NotoSansArabic.txt').write_bytes(read('https://raw.githubusercontent.com/google/fonts/main/ofl/notosansarabic/OFL.txt'))

if __name__=='__main__':main()
