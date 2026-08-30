#!/usr/bin/env bash
# Download placeholder imagery at final crops (Unsplash CDN). Verify each file after download.
set -u
cd "D:/work/merdian/ox 2/assets/img"
dl () { # name id w h
  curl -sL --max-time 60 -o "$1.jpg" "https://images.unsplash.com/$2?w=$3&h=$4&fit=crop&crop=entropy&q=80&auto=format"
}
dl hero-home        photo-1541888946425-d81bb19240f5 2400 1350
dl hero-about       photo-1503387762-592deb58ef4e   2400 1000
dl hero-services    photo-1487958449943-2429e8be8625 2400 1000
dl hero-projects    photo-1486406146926-c627a92ad1ab 2400 1000
dl hero-disciplines photo-1465447142348-e9952c393450 2400 1000
dl proj-awqad       photo-1507525428034-b723cf961d3e 1600 1200
dl proj-albahjal    photo-1566073771259-6a8506099945 1600 1200
dl proj-salalah     photo-1520250497591-112f2f40a3f4 1600 1200
dl proj-redan       photo-1551882547-ff40c63fe5fa    1600 1200
dl proj-alsalam     photo-1515263487990-61b07816b324 1600 1200
dl proj-restaurant  photo-1517248135467-4c7edcad34c4 1600 1200
dl about-story      photo-1504307651254-35680f356dfd 1200 1400
ls -la *.jpg | awk '{print $5, $9}'
python - <<'PY'
from PIL import Image
import glob
for f in sorted(glob.glob(r"D:/work/merdian/ox 2/assets/img/*.jpg")):
    try:
        im = Image.open(f); im.verify()
        im2 = Image.open(f)
        print(f.split("\\")[-1], im2.size, im2.mode)
    except Exception as e:
        print("BAD:", f, e)
PY