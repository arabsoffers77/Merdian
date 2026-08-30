#!/usr/bin/env python3
"""Static-site link/asset/anchor auditor.

Run from the site root:  python link_audit.py

Checks, across every top-level *.html page:
  1. Every href/src that is a local file path resolves to an existing file.
  2. Every same-page "#anchor" has a matching id= in that page.
  3. Every cross-page "page.html#anchor" has a matching id= in the target page.
  4. Leftover typo tokens sweep (edit BAD_TOKENS per project).

Exit message ends with 'problems: N' — require 0 before delivery.
"""
import glob
import os
import re

BAD_TOKENS = ['labeL>', 'scrub-block', '<div quality', 'design-card']

os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
os.chdir('..') if os.path.basename(os.getcwd()) == '_dev-tools' else None
# If not run from site root, try one level up (common layouts).
if not glob.glob('*.html'):
    os.chdir('..')

pages = sorted(glob.glob('*.html'))
problems = []
checked = 0

for page in pages:
    html = open(page, encoding='utf-8').read()
    for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
        if ref.startswith(('http', '#', 'mailto:', 'tel:', 'data:')):
            continue
        checked += 1
        path = ref.split('#')[0].split('?')[0]
        if path and not os.path.exists(path):
            problems.append(f'{page}: MISSING FILE -> {ref}')
    ids = set(re.findall(r'id="([^"]+)"', html))
    for ref in re.findall(r'href="#([^"]+)"', html):
        if ref and ref not in ids:
            problems.append(f'{page}: DEAD ANCHOR -> #{ref}')

for page in pages:
    html = open(page, encoding='utf-8').read()
    for target, anchor in re.findall(r'href="([a-z]+\.html)#([^"]+)"', html):
        if os.path.exists(target):
            target_html = open(target, encoding='utf-8').read()
            if f'id="{anchor}"' not in target_html:
                problems.append(f'{page}: CROSS-PAGE DEAD ANCHOR -> {target}#{anchor}')
        else:
            problems.append(f'{page}: CROSS-PAGE TARGET MISSING -> {target}')

for page in pages:
    html = open(page, encoding='utf-8').read()
    for tok in BAD_TOKENS:
        if tok in html:
            problems.append(f'{page}: LEFTOVER TOKEN "{tok}"')

placeholders = sum(open(p, encoding='utf-8').read().count('PLACEHOLDER') for p in pages)

print(f'pages scanned : {len(pages)}')
print(f'file refs     : {checked}')
print(f'placeholder markers: {placeholders}')
print(f'problems      : {len(problems)}')
for p in problems:
    print(' -', p)
