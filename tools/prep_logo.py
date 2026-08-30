# -*- coding: utf-8 -*-
"""Process MEC logo: trim white margins -> trimmed JPG + transparent PNG + favicon; sample brand colors."""
from PIL import Image
import numpy as np

SRC = r"C:\Users\ASUS\AppData\Roaming\Hermes\composer-images\composer_2026-08-25_01-15-08-813_4eb39d.jpg"
OUT = r"D:\work\merdian\ox 2\assets\img"

img = Image.open(SRC).convert("RGB")
a = np.asarray(img).astype(int)
print("original size:", img.size)

# non-white bounding box (threshold: any channel < 245 counts as ink)
mask = (a < 245).any(axis=2)
rows = np.where(mask.any(axis=1))[0]
cols = np.where(mask.any(axis=0))[0]
pad = 6  # small breathing pad
top, bottom = max(rows[0]-pad, 0), min(rows[-1]+pad, a.shape[0])
left, right = max(cols[0]-pad, 0), min(cols[-1]+pad, a.shape[1])
print("bbox:", left, top, right, bottom)

trimmed = img.crop((left, top, right, bottom))
trimmed.save(OUT + r"\logo.jpg", quality=92)
print("logo.jpg:", trimmed.size)

# transparent PNG: near-white pixels -> alpha 0, soft edge via luminance ramp
t = np.asarray(trimmed.convert("RGB")).astype(int)
lum = t.mean(axis=2)
alpha = np.clip((248 - lum) / (248 - 200) * 255, 0, 255).astype(np.uint8)
rgba = np.dstack([t.astype(np.uint8), alpha])
Image.fromarray(rgba, "RGBA").save(OUT + r"\logo.png")

# favicon: hexagon mark zone only — take upper ~62% of the artwork (icon above wordmark), square-cropped center
h = trimmed.size[1]
icon_zone = trimmed.crop((0, 0, trimmed.size[0], int(h * 0.62)))
w2, h2 = icon_zone.size
side = min(w2, h2)
fx, fy = (w2 - side)//2, (h2 - side)//2
fav = icon_zone.crop((fx, fy, fx+side, fy+side)).resize((64, 64), Image.LANCZOS)
fav.save(r"D:\work\merdian\ox 2\assets\img\favicon.png")
print("favicon ok")

def hexof(px):
    return "#%02X%02X%02X" % tuple(int(v) for v in px)

# color sampling: strongest saturated pixel cluster = amber; darkest cluster = grey 'm'
mx = t.max(axis=2); mn = t.min(axis=2)
sat = mx - mn
amber_px = t[sat > 60]
if len(amber_px):
    med = np.median(amber_px.reshape(-1, 3), axis=0)
    print("AMBER sampled:", hexof(med))
dark_px = t[(lum < 120) & (sat <= 40)]
if len(dark_px):
    med = np.median(dark_px.reshape(-1, 3), axis=0)
    print("DARKGREY sampled:", hexof(med))
mid_grey = t[(lum >= 120) & (lum < 200) & (sat <= 30)]
if len(mid_grey):
    print("MIDGREY count:", len(mid_grey), "median:", hexof(np.median(mid_grey.reshape(-1,3), axis=0)))
