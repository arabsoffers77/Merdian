"""Small static-media helpers. No service, framework, API key or build dependency."""
from functools import lru_cache
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def catalog():
    return json.loads((ROOT/'assets/media/catalog.json').read_text(encoding='utf8'))

def image_tag(key, alt=None, lazy=True, sizes='100vw', priority=False):
    item = next(p for p in catalog()['projects'] if p['key']==key)
    variants = item['variants']
    fallback = min(variants,key=lambda v:abs(v['width']-960))
    srcset = ', '.join(f"{v['src']} {v['width']}w" for v in variants)
    loading = 'lazy' if lazy else 'eager'
    extra = ' fetchpriority="high"' if priority else ''
    return (f'<img class="client-photo" src="{fallback["src"]}" srcset="{srcset}" sizes="{escape(sizes,quote=True)}" '
            f'width="{item["width"]}" height="{item["height"]}" alt="{escape(alt or item["alt"],quote=True)}" '
            f'loading="{loading}" decoding="async"{extra} style="object-position:{item.get("position","50% 50%")}">')

def project_tuples():
    items = catalog()['projects']
    order = catalog()['featured']
    ordered = [next(p for p in items if p['key']==key) for key in order]
    ordered += [p for p in items if p['key'] not in order]
    return [(p['key'],escape(p['name']),p['kind'],p['key'],p['category'],
             escape(p['summary']),escape(p['description'],quote=True)) for p in ordered]

def full_image(key):
    return next(p['variants'][-1]['src'] for p in catalog()['projects'] if p['key']==key)

def hero_film():
    video = catalog()['video']
    pw,ph=video['poster_width'],video['poster_height']
    desktop=video['outputs']['desktop']
    return f'''<figure class="hero-media hero-video">
    <img class="hero-poster client-photo" src="{video['poster']}" srcset="{video['poster_mobile']} 800w, {video['poster']} {pw}w" sizes="(max-width: 700px) 100vw, 85vw" width="{pw}" height="{ph}" alt="{escape(video['alt'],quote=True)}" fetchpriority="high" decoding="async">
    <video id="hero-film" class="client-photo" muted loop playsinline preload="none" width="{desktop['width']}" height="{desktop['height']}" aria-label="{escape(video['alt'],quote=True)}" data-src="{video['desktop']}" data-src-mobile="{video['mobile']}"></video>
    <figcaption class="video-badge">{escape(video['label'])}</figcaption>
    <button class="video-toggle" type="button" aria-controls="hero-film" aria-label="Play project film">Play film</button>
    <noscript><video class="hero-film-manual" controls playsinline preload="none" poster="{video['poster']}"><source src="{video['mobile']}" type="video/mp4"></video></noscript>
  </figure>'''
