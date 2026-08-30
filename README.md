# Meridian Engineering Consultancy — Website ("ox 2" build)

Static, animation-rich redesign · 6 pages · no framework · ready for Hostinger.
Design direction: **"Blueprint Grid"** — white-dominant pages framed by hairline
drafting lines, joined cells on shared borders, amber accent used only on CTAs,
hover states, active nav and small underlines.

## Files & folders
```
index.html / about.html / services.html / projects.html / disciplines.html / contact.html
assets/css/style.css      design system (tokens at top of file)
assets/js/main.js         GSAP layer: reveals, hero split, counters, rows, filters, form, page fade
assets/vendor/            gsap.min.js + ScrollTrigger.min.js (vendored — no CDN dependency)
assets/img/               logo.png/jpg, favicon.png, placeholder photography
tools/build.py            SINGLE SOURCE OF TRUTH — regenerates all 6 pages
tools/link_audit.py       verifies every href/src/anchor resolves        (problems must be 0)
tools/shoot.py            CDP screenshots of all pages -> _verify/
tools/interact_test.py    interaction tests (rows, nav, filters, form)
tools/reduced_motion_test.py  accessibility check
_verify/                  latest desktop+mobile renders (evidence)
```

## Editing content
Do NOT edit the .html files by hand for shared changes (nav/footer/icons) — edit
`tools/build.py` and re-run:
```
python tools/build.py && python tools/link_audit.py
```
Page-specific copy can be edited directly in build.py's page functions too.

## Deploying to Hostinger
Upload everything EXCEPT `tools/`, `_verify/`, `README.md` into `public_html`.
No server-side requirements — pure static hosting works as-is.

## Replacing placeholders (all marked in HTML comments)
| Item | Marker | Action |
|---|---|---|
| Project photos | `<!-- PLACEHOLDER IMAGE -->` | drop client photo over `assets/img/proj-*.jpg` (1600×1200) |
| Page heroes | same | overwrite `assets/img/hero-*.jpg` (2400×1000; home 2400×1350) |
| Hero video | `<!-- PLACEHOLDER VIDEO -->` | add `<video autoplay muted loop playsinline>` inside `.hero-video` figure |
| Social links | `#` + `<!-- PLACEHOLDER: add real social URL -->` | one-line href swap in footer/contact (icons already functional) |
| Stats numbers | `<!-- PLACEHOLDER NUMBERS: confirm stats with client -->` | about.html STATS block |
| Timeline dates | `<!-- PLACEHOLDER MILESTONES -->` | about.html TIMELINE block |
| Client names | `<!-- PLACEHOLDER: confirm client name -->` | projects.html cards (only Dhofar Municipality is confirmed) |
| Map | `<!-- PLACEHOLDER MAP -->` | replace Google Maps embed q= with exact coordinates |
| Working hours | `<!-- PLACEHOLDER -->` in contact info cell | confirm with client |

## Contact form
Currently validate-only (client-side). To receive real submissions, connect to
Formspree or Web3Forms: create a form endpoint, then in `main.js` `initForm()`
POST the FormData to your endpoint URL inside the success branch. No other change.

## Animation spec implemented (per brief §5)
- Engine: GSAP 3.12 + ScrollTrigger (vendored locally)
- Reveals: fade-up 760–800ms, power2.out, stagger 100ms, fire-once at top 86%
- Hero: word-split 1150ms @70ms stagger · Ken Burns 18s yoyo · scroll-expansion 74%→100%
- Hovers: 220–340ms ease-out; expandable rows 300ms height+fade
- Nav: transparent→solid at scroll; page transitions 260ms fade
- Timeline: 3D flip cards (hover/tap/keyboard) · wrapping grid — all 5 always visible
- prefers-reduced-motion: everything appears instantly, transforms disabled

## Verification status (2026-08-25)
- link_audit: problems 0
- interactions: rows / nav / filters(visual) / modal / flip-cards / form — PASS ×6
- overflow audit: 0 page-level horizontal overflow on all pages at 1440/768/390
- timeline grid: 5 cards fully visible at 1440 (5-col) / 820 (3+2) / 390 (stacked), no overflow
- reduced motion: 0 hidden elements across all 6 pages
- CDP renders: 12 screenshots (desktop+mobile) visually audited
