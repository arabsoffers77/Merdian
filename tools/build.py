# -*- coding: utf-8 -*-
"""
Meridian Engineering Consultancy — static site generator ("Blueprint Grid" direction).
Run:  python tools/build.py   -> emits 6 .html pages at repo root.
Single source of truth: header/footer/icons shared; edit here, rebuild everywhere.
"""
import os
import html as _html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- icons ----
PATHS = {
    "compass":   '<circle cx="12" cy="12" r="9"/><path d="M15 9l-2 4.5L8.5 15l2-4.5z"/>',
    "bolt":      '<path d="M13 3L5.5 13H11l-1 8L18.5 11H13l1-8z"/>',
    "award":     '<circle cx="12" cy="9" r="5"/><path d="M9.7 13.6L8 21l4-2.3L16 21l-1.7-7.4"/>',
    "shield":    '<path d="M12 3l7 2.8v5.4c0 4.5-2.9 7.4-7 8.8-4.1-1.4-7-4.3-7-8.8V5.8z"/><path d="M9 11.6l2.1 2.1 4.2-4.2"/>',
    "crosshair": '<circle cx="12" cy="12" r="7"/><path d="M12 2.5V6M12 18v3.5M2.5 12H6M18 12h3.5"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
    "clipboard": '<rect x="5" y="4.5" width="14" height="16.5" rx="2"/><path d="M9 4.5a3 3 0 0 1 6 0"/><path d="M9 13l2 2 4-4.5"/>',
    "draft":     '<path d="M4 20l1.2-4.2L16.6 4.4a2.1 2.1 0 0 1 3 3L8.2 18.8 4 20z"/><path d="M14.6 6.4l3 3"/>',
    "helmet":    '<path d="M4.5 16a7.5 7.5 0 0 1 15 0"/><path d="M2.8 16h18.4"/><path d="M12 8.5V6"/>',
    "plan":      '<rect x="4" y="4" width="16" height="16" rx="1"/><path d="M12 4v16M4 12h16"/>',
    "building":  '<rect x="5" y="3" width="14" height="18" rx="1"/><path d="M9 7h2m2 0h2M9 11h2m2 0h2M9 15h2m2 0h2"/><path d="M10.5 21v-3.5h3V21"/>',
    "gantt":     '<path d="M4 6.5h11M7 12h11M4 17.5h8"/><circle cx="4" cy="6.5" r=".9" fill="currentColor" stroke="none"/><circle cx="7" cy="12" r=".9" fill="currentColor" stroke="none"/><circle cx="4" cy="17.5" r=".9" fill="currentColor" stroke="none"/>',
    "signal":    '<rect x="8.5" y="2.5" width="7" height="19" rx="3.5"/><circle cx="12" cy="7" r="1.3" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/><circle cx="12" cy="17" r="1.3" fill="currentColor" stroke="none"/>',
    "road":      '<path d="M6.5 21L9.8 3h4.4L17.5 21"/><path d="M12 7v2.2M12 12v2.2M12 17v2.2"/>',
    "droplet":   '<path d="M12 3s6 6.4 6 10.8A6 6 0 0 1 6 13.8C6 9.4 12 3 12 3z"/>',
    "skyline":   '<path d="M3 21h18"/><path d="M5 21V8.5L10 6v15"/><path d="M14 21V11l5-2v12"/>',
    "highway":   '<path d="M5.5 21L10 3"/><path d="M18.5 21L14 3"/><path d="M12 6.5v2M12 11.5v2M12 16.5v2"/>',
    "bridge":    '<path d="M2 13.5h20"/><path d="M5.5 18.5a6.5 6.5 0 0 1 13 0"/><path d="M5.5 13.5v5M18.5 13.5v5"/><path d="M2 18.5h3.5M18.5 18.5H22"/>',
    "tunnel":    '<path d="M4.5 20.5V14a7.5 7.5 0 0 1 15 0v6.5"/><path d="M9 20.5v-4a3 3 0 0 1 6 0v4"/><path d="M2 20.5h20"/>',
    "plane":     '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/>',
    "train":     '<rect x="6" y="3" width="12" height="14" rx="3"/><path d="M6 9.5h12"/><circle cx="9.2" cy="19" r="1.5"/><circle cx="14.8" cy="19" r="1.5"/><path d="M8 17l-2.2 3.5M16 17l2.2 3.5"/>',
    "dam":       '<path d="M5 3v18"/><path d="M8.2 3v18"/><path d="M12.5 9c1.8 1.4 3.6 1.4 5.4 0 1.4-1.1 2.8-1.2 4.1-.3"/><path d="M12.5 14c1.8 1.4 3.6 1.4 5.4 0 1.4-1.1 2.8-1.2 4.1-.3"/><path d="M12.5 19c1.8 1.4 3.6 1.4 5.4 0 1.4-1.1 2.8-1.2 4.1-.3"/>',
    "pipe":      '<path d="M5 3.5v5.5a5 5 0 0 0 5 5h8.5"/><path d="M18.5 14v6.5"/><path d="M3.2 6h3.6M3.2 9.5h3.6"/>',
    "flame":     '<path d="M12 3c.8 3 4 4.6 4 8.2A4.8 4.8 0 0 1 12 16a4.8 4.8 0 0 1-4-4.8c0-1.8.8-3.2 1.8-4.6.3 1.2 1 2.1 2.1 2.6C11.4 7 11.6 4.8 12 3z"/>',
    "mail":      '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 7.5l8.5 5.7 8.5-5.7"/>',
    "phone":     '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z"/>',
    "pin":       '<path d="M20 10.2c0 5.8-8 11.8-8 11.8s-8-6-8-11.8a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="2.6"/>',
    "clock":     '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "arrow":     '<path d="M4.5 12h14"/><path d="M13 6.5l5.5 5.5-5.5 5.5"/>',
    "info":      '<circle cx="12" cy="12" r="8.5"/><path d="M12 8h.01M12 11.2V16"/>',
    "check":     '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.4l2.4 2.4 4.8-5"/>',
    "refresh":   '<path d="M17 2.5l3.5 3.5-3.5 3.5"/><path d="M3.5 11V9.5A3.5 3.5 0 0 1 7 6h13.5"/><path d="M7 21.5L3.5 18 7 14.5"/><path d="M20.5 13v1.5a3.5 3.5 0 0 1-3.5 3.5H3.5"/>',
}

def ic(name, cls="cell-icon"):
    return ('<svg class="' + cls + '" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + PATHS[name] + "</svg>")

PLAY_SVG = '<svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>'
SOCIALS = {
    "LinkedIn": '<svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4V9h4v1.3A5 5 0 0 1 16 8z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>',
    "X": '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M17.7 3H21l-7.2 8.3L22.2 21h-6.6l-5.2-6.1L4.6 21H1.3l7.7-8.9L1.8 3h6.8l4.7 5.6L17.7 3zm-1.2 16h1.8L7.6 4.9H5.7L16.5 19z"/></svg>',
    "Instagram": '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1.2" fill="currentColor" stroke="none"/></svg>',
    "Facebook": '<svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-7h2.4l.4-3h-2.8V9.1c0-.9.3-1.5 1.6-1.5h1.3V4.9c-.6-.1-1.4-.2-2.3-.2-2.3 0-3.8 1.4-3.8 3.9V11H8v3h2.3v7z"/></svg>',
}

# ---------------------------------------------------------------- content --
NAV = [
    ("index.html", "Home"),
    ("about.html", "About Us"),
    ("services.html", "Services"),
    ("projects.html", "Projects"),
    ("disciplines.html", "Disciplines"),
    ("contact.html", "Contact Us"),
]

DISCIPLINES = [
    ("buildings", "Buildings", "skyline",
     "Residential, commercial and institutional buildings designed and supervised to international codes and Omani authority requirements.",
     ["Residential", "Commercial", "Institutional", "Mixed-use", "Interior fit-out"]),
    ("roads-highways", "Roads &amp; Highways", "highway",
     "Geometric design, pavement engineering and traffic infrastructure for arterial roads, highways and interchange systems.",
     ["Geometric design", "Pavement engineering", "Drainage", "Interchanges", "Utilities corridor"]),
    ("bridges", "Bridges", "bridge",
     "Reinforced concrete, prestressed and steel bridge structures — from alignment studies to load rating and inspection.",
     ["RC &amp; prestressed", "Steel structures", "Inspection", "Load rating", "Rehabilitation"]),
    ("tunnels", "Tunnels", "tunnel",
     "Cut-and-cover and bored tunnel solutions with full ventilation, fire-life-safety and lining design coordination.",
     ["Cut-and-cover", "Bored tunnels", "Ventilation", "Fire &amp; life safety", "Lining design"]),
    ("airports", "Airports", "plane",
     "Airside and landside planning and design — runways, taxiways, aprons and terminal-supporting infrastructure.",
     ["Runways &amp; taxiways", "Aprons", "Terminal planning", "Airside drainage", "NAVAID coordination"]),
    ("railways", "Railways", "train",
     "Track alignment, stations, depots and systems coordination for passenger and freight rail developments.",
     ["Track alignment", "Stations", "Depots", "Signalling coordination", "Level crossings"]),
    ("water-sanitation", "Water Supply &amp; Sanitation", "droplet",
     "Transmission mains, distribution networks, reservoirs and pumping stations delivering reliable potable water.",
     ["Transmission mains", "Distribution networks", "Reservoirs", "Pumping stations", "Demand modelling"]),
    ("dams", "Dams", "dam",
     "Embankment and gravity dam design with hydrological studies, spillway works and impoundment safety.",
     ["Embankment dams", "Gravity dams", "Spillways", "Hydrology", "Impoundment safety"]),
    ("sewage", "Sewage", "pipe",
     "Foul sewer networks, lift stations and treatment process support serving communities and industry.",
     ["Sewer networks", "Lift stations", "Treatment processes", "Outfalls", "Odour control"]),
    ("oil-gas", "Oil &amp; Gas", "flame",
     "Site development, tank farms and utility infrastructure supporting energy sector facilities and maintenance programmes.",
     ["Site development", "Tank farms", "Utilities", "Pipe racks", "Maintenance support"]),
]

SERVICES = [
    ("feasibility", "Feasibility Studies", "clipboard",
     "Technical and commercial viability established before capital is committed — so decisions rest on evidence, not assumption.",
     ["Site assessment", "Demand analysis", "Cost modelling", "Regulatory review", "Risk register"]),
    ("design", "Detailed Engineering Design", "draft",
     "Fully coordinated multidisciplinary design packages taken to construction readiness with complete tender documentation.",
     ["Civil &amp; structural", "MEP design", "Tender documents", "BOQ &amp; specifications", "Design reviews"]),
    ("supervision", "Construction Supervision", "helmet",
     "Resident engineers on site safeguarding quality, safety, programme and contractor coordination through to handover.",
     ["Resident engineering", "QA/QC inspections", "Progress reporting", "Safety oversight", "Handover files"]),
    ("urban", "Urban Planning", "plan",
     "Master plans that reconcile land use, movement, infrastructure and community needs into coherent, buildable frameworks.",
     ["Master plans", "Land-use strategy", "Infrastructure planning", "Urban design guidelines"]),
    ("architecture", "Architectural Design", "building",
     "Context-driven building design developed from first sketches to detailed architectural packages ready for construction.",
     ["Concept design", "Space planning", "Facade &amp; materials", "Detailed packages"]),
    ("pm", "Project Management", "gantt",
     "End-to-end management of time, cost, scope and risk across every project phase, from briefing to closeout.",
     ["Programming", "Cost control", "Procurement support", "Risk management", "Client reporting"]),
    ("traffic", "Traffic Impact Studies", "signal",
     "Evidence-based analysis of how a development affects the surrounding road network — with practical mitigation.",
     ["Trip generation", "Junction analysis", "Access design", "Mitigation plans"]),
    ("rsa", "Road Safety Auditing", "road",
     "Independent audits of road schemes at every design stage and after construction, focused on all road users.",
     ["Stage 1–4 audits", "Site inspections", "Collision review", "Remedial advice"]),
]

PROJECTS = [
    ("awqad", "Awqad Beach", "Dhofar Municipality", "proj-awqad", "urban-planning buildings",
     "Coastal development study and design for a flagship public waterfront.",
     "A coastal development commission for Dhofar Municipality covering the Awqad Beach frontage — master-plan framework, beachfront access and promenade design, utilities routing and phased implementation advice, balancing public amenity with the sensitivity of the shoreline environment."),
    ("albahjal", "Albahjal Hotel", "Private Developer", "proj-albahjal", "buildings hospitality",
     "Boutique hotel architecture and engineering in an urban setting.",
     "Full architectural and engineering package for a boutique urban hotel — guest-room layouts, facade treatment, MEP coordination and authority approvals, carried through construction-stage supervision to fit-out handover."),
    ("salalah", "Grand Salalah Resort", "Hospitality Group", "proj-salalah", "hospitality buildings",
     "Resort master planning, design coordination and site supervision.",
     "Master plan and design coordination for a destination resort in Dhofar — villa siting around landscape features, pool and amenity structures, infrastructure networks and multidisciplinary site supervision across all construction packages."),
    ("alsalam", "Alsalam Town", "Private Developer", "proj-alsalam", "urban-planning",
     "Integrated township framework — land use, infrastructure and streetscape.",
     "An integrated township framework defining land-use parcels, road hierarchy and open-space network, with utility corridor planning and streetscape guidelines that let later phases proceed without re-engineering earlier ones."),
    ("redan", "Redan Hotel", "Private Developer", "proj-redan", "buildings hospitality",
     "Hotel building design and construction-stage engineering support.",
     "Design and construction-stage engineering for a city hotel building — structural and architectural packages, room-module standardisation for operational efficiency, and resident engineering support through to completion."),
    ("restaurant", "Restaurant Project", "Private Client", "proj-restaurant", "buildings hospitality",
     "Bespoke dining venue — architecture, interiors and services design.",
     "A bespoke dining venue delivered end-to-end — interior architecture, kitchen and services design, ventilation and acoustic treatment, and authority submissions, coordinated to a tight fit-out programme."),
]
# NOTE: client names other than Dhofar Municipality are placeholders — confirm with client.

PILLARS = [
    ("Creativity", "compass", "Fresh engineering responses to complex sites and demanding briefs."),
    ("Efficiency", "bolt", "Lean delivery that respects budget and programme alike."),
    ("Excellence", "award", "Standards applied uniformly, from first concept to final handover."),
    ("Quality", "shield", "Documented QA/QC embedded in every stage of every project."),
    ("Precision", "crosshair", "Decisions grounded in survey data, codes and calculation."),
]

VALUES = ["Quality", "Integrity", "Teamwork", "Staff Motivation", "Sustainability"]

STATS = [  # PLACEHOLDER NUMBERS: confirm stats with client before launch
    ("15", "+", "Years of practice"),
    ("120", "+", "Projects delivered"),
    ("10", "", "Core disciplines"),
    ("6", "+", "International associations"),
]

TIMELINE = [  # PLACEHOLDER MILESTONES: confirm dates with client
    ("2009", "Founded in Muscat", "Where it began.",
     "MEC registered in Oman as a multi-disciplinary consultancy — engineers, planners and project managers under one roof from day one."),
    ("2013", "First international association", "Going global.",
     "Partnership formed with a specialised European design firm, pairing deep technical capacity with Omani market knowledge."),
    ("2016", "Dhofar portfolio grows", "Southward reach.",
     "Municipal and tourism commissions expand our work beyond Muscat — coastal, hospitality and public-realm projects across the governorate."),
    ("2020", "QA systems aligned to ISO", "Raised standards.",
     "Documented quality management embedded across every stage, aligning design deliverables and site supervision with international practice."),
    ("2024", "Ten disciplines, three continents", "Full spectrum.",
     "Associations across Europe, USA, Asia &amp; Africa now support major bids across all ten core disciplines."),
]

ADDRESS = "Ehssan Street, Road 3904, Block 439, Building 234, Al Amerat, Muscat, Oman"
EMAIL = "info@meridianengconsultants.com"
PHONE_DISPLAY = "+968 9700 4250"
PHONE_TEL = "+96897004250"

# ---------------------------------------------------------------- chrome ---
def head_block(title, desc):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="icon" type="image/png" href="assets/img/favicon.png">
<script>document.documentElement.classList.add('js');</script>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <defs>
    <!-- Regular POINTY-TOP hexagon — geometry measured from the actual
         logo pixels (h/w = 1.1545, full width at 25-75% height) -->
    <clipPath id="mecHexClip" clipPathUnits="objectBoundingBox">
      <path d="M0.4821,0.0088 Q0.5000,0.0000 0.5179,0.0088 L0.9821,0.2372 Q1.0000,0.2460 1.0000,0.2660 L1.0000,0.7340 Q1.0000,0.7540 0.9821,0.7628 L0.5179,0.9912 Q0.5000,1.0000 0.4821,0.9912 L0.0179,0.7628 Q0.0000,0.7540 0.0000,0.7340 L0.0000,0.2660 Q0.0000,0.2460 0.0179,0.2372 Z"/>
    </clipPath>
  </defs>
</svg>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&amp;family=Manrope:wght@400;500;600;700&amp;display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&amp;family=Manrope:wght@400;500;600;700&amp;display=swap" rel="stylesheet"></noscript>
<link rel="stylesheet" href="assets/css/style.css?v=20260903a">
</head>
'''

def header(active):
    links = ""
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        links += f'        <li><a class="nav-link" href="{href}"{cur}>{label}</a></li>\n'
    return f'''<header class="site-header">
  <div class="wrap">
    <a href="index.html" class="brand" aria-label="Meridian Engineering Consultancy — Home">
      <img src="assets/img/logo.png" alt="Meridian Engineering Consultancy logo — amber hexagon with grey m and MERIDIAN wordmark" class="logo-img" width="34" height="46">
    </a>
    <nav class="main-nav" aria-label="Primary">
      <ul>
{links}      </ul>
    </nav>
    <button class="nav-toggle" aria-label="Toggle navigation menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>
'''

def socials_html():
    out = ['<div class="socials" aria-label="Meridian on social media">']
    for name, svg in SOCIALS.items():
        out.append(f'''<a href="#" aria-label="Meridian on {name}" title="{name}" rel="noopener"><!-- PLACEHOLDER: add real social URL -->{svg}</a>''')
    out.append("</div>")
    return "\n".join(out)

def footer(extra_scripts=""):
    nav_links = "".join(f'<li><a href="{h}">{l}</a></li>' for h, l in NAV[1:])
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-main">
      <div>
        <img src="assets/img/logo.png" alt="Meridian Engineering Consultancy logo" class="logo-img" width="30" height="42" loading="lazy">
        <p style="margin-top:16px;">Multi-disciplinary engineering consultancy registered in Oman — delivering innovative engineering and lasting solutions.</p>
{socials_html()}
      </div>
      <div>
        <h4>Explore</h4>
        <ul class="footer-links">
          {nav_links}
        </ul>
      </div>
      <div>
        <h4>Contact</h4>
        <address>{ADDRESS}</address>
        <p style="margin-top:12px;"><a href="mailto:{EMAIL}">{EMAIL}</a><br>
        <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></p>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year>2026</span> Meridian Engineering Consultancy. All rights reserved.</span>
      <span class="crumbs"><span>Muscat · Al Amerat, Oman</span><a href="#top">Back to top</a></span>
    </div>
  </div>
</footer>
<script src="assets/vendor/gsap.min.js?v=20260903a" defer></script>
<script src="assets/vendor/ScrollTrigger.min.js?v=20260903a" defer></script>
<script src="assets/js/main.js?v=20260903a" defer></script>
{extra_scripts}</body>
</html>
'''

def arrow_link(label, href):
    return f'<a class="text-link" href="{href}">{label}<span class="arr">{ic("arrow","arr")}</span></a>'

def slide_btn(label, hover_label, href, solid=True):
    """KokonutUI-style slide-text button: label rolls up, alt label rolls in."""
    cls = "btn btn--solid" if solid else "btn"
    return (f'<a class="{cls}" href="{href}">'
            f'<span class="slide-txt">'
            f'<span class="st-row"><span>{label}</span>&nbsp;{ic("arrow","arr")}</span>'
            f'<span class="st-row st-b" aria-hidden="true">{hover_label}</span>'
            f'</span></a>')

def cta_band():
    return f'''<section class="section">
  <div class="wrap">
    <div class="cta-band" data-reveal>
      <div>
        <h2>Have a project in mind?</h2>
        <p class="lede">From first feasibility study to final handover certificate — talk to a team that delivers across ten disciplines.</p>
      </div>
      <div style="display:flex;gap:14px;flex-wrap:wrap;">
        {slide_btn("Contact Us", "Start a project", "contact.html")}
        <a class="btn" href="tel:{PHONE_TEL}">{ic("phone")}&nbsp;{PHONE_DISPLAY}</a>
      </div>
    </div>
  </div>
</section>
'''

def ticker():
    items = "".join(f"<li>{d[1]}</li>" for d in DISCIPLINES)
    return f'''<section class="ticker-section" aria-label="Disciplines ticker">
  <div class="ticker">
    <div class="ticker-track">
      <ul class="ticker-seq">{items}</ul>
      <ul class="ticker-seq" aria-hidden="true">{items}</ul>
    </div>
  </div>
</section>
'''

def page_hero(eyebrow, title, lede, img, alt, index_label, after_lede=''):
    return f'''<section class="page-hero">
  <div class="wrap">
    <div class="page-hero-grid">
      <div class="page-hero-copy">
        <p class="eyebrow">{eyebrow}</p>
        <h1 class="display-lg">{title}</h1>
        <p class="lede" style="margin-top:18px;">{lede}</p>
        {after_lede}
        <div class="ph-meta"><span>Meridian Engineering Consultancy</span><b>{index_label}</b></div>
      </div>
      <div class="page-hero-media">
        <!-- PLACEHOLDER IMAGE: replace with client project photo -->
        <img src="assets/img/{img}" alt="{alt}" fetchpriority="high">
      </div>
    </div>
  </div>
</section>
'''

def proj_card(p, span_cls, lazy=True, chroma=False):
    """chroma=True (home Selected Work) adds the pointer-spotlight treatment:
    card always fully visible; hover adds amber border-glow + veil deepens."""
    key, name, client, img, cat, blurb, desc = p
    cat_label = cat.replace("-", " ").title()
    lazy_attr = ' loading="lazy"' if lazy else ""
    cls = f'proj-card chroma-card {span_cls}' if chroma else f'proj-card {span_cls}'
    veil = '<div class="chroma-veil"></div>' if chroma else ''
    return f'''<a class="{cls}" id="proj-{key}" href="#proj-{key}" data-category="{cat}" data-reveal-child data-name="{name}" data-client="{client}" data-cat-label="{cat_label}" data-desc="{desc}">
  <div class="proj-media">
    <!-- PLACEHOLDER IMAGE: replace with client project photo — {name} -->
    <img src="assets/img/{img}.jpg" alt="{name} — representative project image"{lazy_attr}>
    {veil}
    <div class="proj-overlay">
      <span class="proj-cat">{cat_label}</span>
      <h3>{name}</h3>
      <span class="proj-line"></span>
      <p style="color:rgba(255,255,255,.85);font-size:13.5px;">{blurb}</p>
    </div>
  </div>
  <div class="proj-meta">
    <span class="proj-title-line"><h3>{name}</h3></span>
    <span class="proj-client">{client}</span><!-- PLACEHOLDER: confirm client name with client -->
  </div>
</a>'''

def project_modal():
    return '''<div class="pmodal" id="project-modal" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Project details">
  <div class="pmodal-backdrop" data-pmodal-close></div>
  <div class="pmodal-panel" role="document">
    <button class="pmodal-close" type="button" data-pmodal-close aria-label="Close project details">&times;</button>
    <div class="pmodal-media">
      <!-- PLACEHOLDER IMAGE: replace with client project photo -->
      <img id="pm-img" src="" alt="">
    </div>
    <div class="pmodal-body">
      <p class="pmodal-cat" id="pm-cat"></p>
      <h3 id="pm-name"></h3>
      <p class="pmodal-client" id="pm-client"></p><!-- PLACEHOLDER: confirm client name with client -->
      <p class="pmodal-desc" id="pm-desc"></p>
      <p class="pmodal-note">Representative imagery shown — client photography pending.</p>
    </div>
  </div>
</div>
'''

# ---------------------------------------------------------------- pages ----
def page_home():
    b = head_block(
        "Meridian Engineering Consultancy — Innovative Engineering, Lasting Solutions.",
        "MEC is a multi-disciplinary engineering consultancy registered in Oman — feasibility studies, detailed design, construction supervision and more.")
    b += header("index.html")
    b += f'''<main id="top">
<section class="hero">
  <div class="blueprint" aria-hidden="true"></div>
  <div class="wrap hero-inner">
    <div class="hero-head">
      <p class="eyebrow">Welcome to Meridian Engineering Consultancy</p>
      <h1 class="display-xl hero-title">Innovative Engineering, Lasting Solutions.</h1>
      <p class="hero-sub">A multi-disciplinary consulting firm registered in Oman — taking projects from first feasibility study to final construction supervision.</p>
      <div class="hero-ctas">
        {slide_btn("View Projects", "Full portfolio", "projects.html")}
        {slide_btn("Our Story", "Who we are", "about.html", solid=False)}
      </div>
      <div class="scroll-cue"><span class="cue-line"></span><span>Scroll</span></div>
    </div>
  </div>
  <figure class="hero-media hero-video">
    <!-- PLACEHOLDER VIDEO: replace poster with client footage — drop a
         <video autoplay muted loop playsinline> element in this figure
         (assets/videos folder) when the film arrives; keep the 16:8 crop. -->
    <img src="assets/img/hero-home.jpg" alt="Engineers reviewing a large foundation slab on an active construction site" fetchpriority="high">
    <figcaption class="video-badge">{PLAY_SVG}&nbsp;Project reel — placeholder footage</figcaption>
  </figure>
</section>
'''
    b += ticker()
    b += f'''<section class="section about-drift-section" id="about-drift-section">
  <div class="drift-field" id="about-drift" aria-hidden="true">
    <p class="drift-hint">Scroll to explore</p>
  </div>
  <div class="wrap">
    <div class="about-copy about-copy--panel" data-reveal>
      <p class="eyebrow">About Us</p>
      <h2 class="display-lg">Engineering consultancy built on precision.</h2>
      <p class="lede" style="margin-top:18px;">Meridian Engineering Consultancy (MEC) is a multi-disciplinary consulting firm registered in Oman. To ensure outstanding professional services, MEC forms associations with specialized foreign firms from Europe, USA, Asia &amp; Africa as necessary.</p>
      <div class="chip-tags">
        <span><i>◆</i>Quality</span><span><i>◆</i>Integrity</span><span><i>◆</i>Teamwork</span><span><i>◆</i>Staff Motivation</span><span><i>◆</i>Sustainability</span>
      </div>
      <p style="margin-top:30px;">{arrow_link("More about us", "about.html")}</p>
    </div>
  </div>
</section>
<section class="section" style="padding-top:0;">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div>
        <p class="eyebrow">Services</p>
        <h2 class="display-lg">Comprehensive consultancy, end to end.</h2>
      </div>
      <div class="head-action">{arrow_link("All services", "services.html")}</div>
    </div>
    <div class="cells grid-cells-4" data-reveal data-reveal-stagger>
'''
    for i, (_key, name, icon_name, blurb, _tags) in enumerate(SERVICES, 1):
        b += f'''        <div class="cell" data-reveal-child>
          <div class="cell-head">{ic(icon_name)}<span class="num-index">{i:02d}</span></div>
          <h3>{name}</h3>
          <p>{blurb}</p>
        </div>
'''
    b += '''    </div>
  </div>
</section>
<section class="section" style="padding-top:0;">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div>
        <p class="eyebrow">Selected Work</p>
        <h2 class="display-lg">Projects that speak for themselves.</h2>
      </div>
      <div class="head-action">''' + arrow_link("Full portfolio", "projects.html") + '''</div>
    </div>
    <div class="feat-grid">
      <div class="feat-cell span-3" data-reveal-child>''' + proj_card(PROJECTS[0], "ratio-wide", lazy=False, chroma=True) + '''</div>
      <div class="feat-cell span-3" data-reveal-child>''' + proj_card(PROJECTS[1], "ratio-wide", chroma=True) + '''</div>
      <div class="feat-cell span-2" data-reveal-child>''' + proj_card(PROJECTS[2], "ratio-tall", chroma=True) + '''</div>
      <div class="feat-cell span-2" data-reveal-child>''' + proj_card(PROJECTS[3], "ratio-tall", chroma=True) + '''</div>
      <div class="feat-cell span-2" data-reveal-child>''' + proj_card(PROJECTS[4], "ratio-tall", chroma=True) + '''</div>
      <div class="feat-cell span-2" data-reveal-child>''' + proj_card(PROJECTS[5], "ratio-tall", chroma=True) + '''</div>
    </div>
  </div>
</section>
'''
    b += project_modal()
    b += cta_band()
    b += "</main>"
    b += footer('<script src="assets/js/drift-field.js?v=20260903a" defer></script>\n')
    return b

def page_about():
    b = head_block("About Us — Meridian Engineering Consultancy",
                   "The story, vision, values and milestones of MEC — a multi-disciplinary engineering consultancy registered in Oman.")
    b += header("about.html")
    b += page_hero("About Us", "Our Story.",
                   "A firm built on associations, precision and a simple belief: the work should speak for itself.",
                   "hero-about.jpg", "Construction professionals reviewing structural drawings", "01 — THE FIRM")
    b += f'''<main id="top">
<section class="section">
  <div class="wrap">
    <div class="split-2">
      <div data-reveal>
        <p class="eyebrow">Who We Are</p>
        <h2 class="display-md" style="margin-bottom:16px;">A multi-disciplinary consulting firm, registered in Oman.</h2>
        <p class="lede">Meridian Engineering Consultancy (MEC) is a multi-disciplinary consulting firm registered in Oman. In its journey to success, MEC forms associations with other specialized foreign firms from Europe, USA, Asia &amp; Africa as necessary, to ensure providing outstanding engineering consultancy professional services.</p>
        <p class="lede" style="margin-top:16px;">That model lets us scale specialist expertise around each commission — the client deals with one accountable firm, while the delivery team always matches the problem at hand.</p>
        <div class="assoc-flash" data-assoc aria-hidden="true">
          <span class="af-label">Partner firms across</span>
          <span class="af-word"><span class="afw">Europe</span></span>
          <noscript><span class="af-word">Europe · USA · Asia · Africa</span></noscript>
        </div>
      </div>
      <div class="media-frame globe-frame" data-reveal>
        <div class="globe-stage">
          <div class="globe-wrap">
            <canvas id="who-globe" role="img" aria-label="Rotating globe with connection lines from Oman to MEC's partner regions in Europe, USA, Asia and Africa"></canvas>
          </div>
        </div>
        <div class="media-caption"><span>Global associations</span><span>Oman · Europe · USA · Asia · Africa</span></div>
      </div>
    </div>
  </div>
</section>
<section class="section" style="padding-top:0;">
  <div class="wrap">
    <div class="vision-quote" data-reveal>
      <p class="eyebrow">Our Vision</p>
      <p>&ldquo;To be a leading global partner providing the best professional services for better quality of life and sustainable development.&rdquo;</p>
    </div>
    <div data-reveal style="margin-top:44px;display:none;">
      <h2 class="display-md" style="margin-bottom:6px;">Values we work by.</h2>
      <div class="chip-tags">
        <span><i>◆</i>Quality</span><span><i>◆</i>Integrity</span><span><i>◆</i>Teamwork</span><span><i>◆</i>Staff Motivation</span><span><i>◆</i>Sustainability</span>
      </div>
    </div>
  </div>
</section>
<section class="section scrolltext-section">
  <p class="eyebrow" style="padding-left:var(--gutter);">Our Values</p>
  <div class="scrolltext" data-scrolltext aria-label="Our values">
''' + "".join(
        f'    <div class="st-item{" is-active" if i == 0 else ""}"><span>{v}</span></div>\n'
        for i, v in enumerate(VALUES)
    ) + '''  </div>
  <p class="scrolltext-hint">Five commitments behind every deliverable.</p>
</section>
<section class="section" style="padding-top:0;">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div>
        <p class="eyebrow">Our Story</p>
        <h2 class="display-lg">Five principles behind every deliverable.</h2>
      </div>
    </div>
    <div class="cells" data-reveal data-reveal-stagger>
      <div class="pillars-row">
'''
    for name, icon_name, blurb in PILLARS:
        b += f'''        <div class="cell pillar" data-reveal-child>
          {ic(icon_name)}
          <h3>{name}</h3>
          <p>{blurb}</p>
        </div>
'''
    b += '''      </div>
    </div>
  </div>
</section>
<section class="stats-band">
  <div class="wrap">
    <!-- PLACEHOLDER NUMBERS: confirm stats with client -->
    <div class="stats-row" data-reveal data-reveal-stagger>
'''
    for num, suffix, label in STATS:
        suf = f'<span class="stat-suffix">{suffix}</span>' if suffix else ""
        b += f'''        <div class="stat" data-reveal-child>
          <span class="stat-num"><span class="stat-num-val" data-count="{num}">{num}</span>{suf}</span>
          <span class="stat-label">{label}</span>
        </div>
'''
    b += '''    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div>
        <p class="eyebrow">Milestones</p>
        <h2 class="display-lg">The journey so far.</h2>
      </div>
    </div>
    <!-- PLACEHOLDER MILESTONES: confirm dates with client -->
    <!-- 3D flip cards: front = year/title · back = full story (hover, tap, or Enter/Space).
         Wrapping responsive grid — all five always visible at every width. -->
    <div class="timeline" data-reveal data-reveal-stagger>
'''
    for year, title, teaser, story in TIMELINE:
        b += f'''      <div class="flip-card" tabindex="0" role="button" aria-pressed="false" data-reveal-child aria-label="{year} — {title}. Activate to flip for details.">
        <div class="flip-inner">
          <div class="flip-face flip-face--front">
            <span class="tl-year">{year}</span>
            <span class="tl-dot"></span>
            <h3>{title}</h3>
            <p class="flip-teaser">{teaser}</p>
            <span class="flip-hint">{ic("refresh", "")}&nbsp;Details</span>
          </div>
          <div class="flip-face flip-face--back">
            <p class="flip-back-meta">{year} · MILESTONE</p>
            <h3>{title}</h3>
            <p>{story}</p>
          </div>
        </div>
      </div>
'''
    b += '''    </div>
  </div>
</section>
'''
    b += cta_band() + "</main>" + footer('<script src="assets/js/globe.js?v=20260903a" defer></script>\n')
    return b

def xrows(entries):
    rows = ""
    for i, (key, name, icon_name, blurb, tags) in enumerate(entries, 1):
        chips = "".join(f"<li>{t}</li>" for t in tags)
        extra = " Every engagement is scoped, programmed and reported against agreed deliverables." if key != "rsa" or True else ""
        if key == "rsa":
            extra = ""
        rows += f'''      <div class="xrow" id="{key}">
        <button class="xrow-btn" type="button" aria-controls="{key}-panel" aria-expanded="false">
          <span class="xrow-num">{i:02d}</span>
          <span class="xrow-title">{name}</span>
          {ic(icon_name, "xrow-icon")}
          <span class="xrow-plus" aria-hidden="true"></span>
        </button>
        <div class="xrow-panel" id="{key}-panel" role="region" aria-label="{name} details">
          <div class="xrow-panel-in">
            <p>{blurb}{extra}</p>
            <ul>{chips}</ul>
          </div>
        </div>
      </div>
'''
    return rows

def page_services():
    b = head_block("Services — Meridian Engineering Consultancy",
                   "Feasibility studies, detailed engineering design, construction supervision, urban planning, architectural design, project management, traffic studies and road safety auditing.")
    b += header("services.html")
    b += page_hero("Services", "What we do.",
                   "Comprehensive professional engineering consultancy — eight core services, one accountable firm.",
                   "hero-services.jpg", "Modern building facade under a clear sky", "02 — CAPABILITIES")
    b += f'''<main id="top">
<section class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div>
        <p class="eyebrow">Service Lines</p>
        <h2 class="display-lg">Eight services. Select any to expand.</h2>
      </div>
    </div>
    <div class="xrows" data-reveal>
{xrows(SERVICES)}    </div>
    <div class="note-band" data-reveal style="margin-top:40px;">
      {ic("info", "")}
      <p><strong>Also provided:</strong> Hydrological Studies and Sewage &amp; Environmental Impact Assessment Studies — alongside the eight service lines above. Ask us how these integrate into your project scope.</p>
    </div>
  </div>
</section>
'''
    b += project_modal()
    b += cta_band() + "</main>" + footer()
    return b

def page_projects():
    b = head_block("Projects — Meridian Engineering Consultancy",
                   "Selected projects across Oman — coastal developments, hotels, resorts, townships and hospitality venues.")
    b += header("projects.html")
    b += page_hero("Portfolio", "Selected Work.",
                   "Real projects across Oman's public and private sectors — imagery shown is placeholder until client photography arrives.",
                   "hero-projects.jpg", "Glass office towers against the sky", "03 — PORTFOLIO")
    b += '''<main id="top">
<section class="section">
  <div class="wrap">
    <div class="filters" role="group" aria-label="Filter projects by discipline" data-reveal>
      <button class="chip is-active" data-filter="*" type="button">All</button>
      <button class="chip" data-filter="buildings" type="button">Buildings</button>
      <button class="chip" data-filter="hospitality" type="button">Hospitality</button>
      <button class="chip" data-filter="urban-planning" type="button">Urban Planning</button>
    </div>
    <div class="projects-grid" data-reveal data-reveal-stagger>
'''
    spans = ["p-span-7 ratio-wide", "p-span-5 ratio-tall",
             "p-span-5 ratio-tall", "p-span-7 ratio-wide",
             "p-span-7 ratio-wide", "p-span-5 ratio-tall"]
    for p, span in zip(PROJECTS, spans):
        b += "      " + proj_card(p, span) + "\n"
    b += '''    </div>
  </div>
</section>
'''
    b += project_modal()
    b += cta_band() + "</main>" + footer()
    return b

def page_disciplines():
    b = head_block("Disciplines — Meridian Engineering Consultancy",
                   "Ten core disciplines — buildings, roads, bridges, tunnels, airports, railways, water, dams, sewage and oil & gas.")
    b += header("disciplines.html")
    b += page_hero("Disciplines", "Ten Disciplines. One Standard.",
                   "The breadth of sectors MEC serves — supported by international associations where specialist depth is required.",
                   "hero-disciplines.jpg", "Long suspension bridge crossing a river valley", "04 — SECTORS")
    b += f'''<main id="top">
<section class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div>
        <p class="eyebrow">Sector Coverage</p>
        <h2 class="display-lg">Select a discipline to see scope.</h2>
      </div>
    </div>
    <div class="xrows" data-reveal>
{xrows(DISCIPLINES)}    </div>
  </div>
</section>
'''
    b += cta_band() + "</main>" + footer()
    return b

def page_contact():
    options = "".join(f'                  <option>{d[1].replace("&amp;", "&")}</option>\n' for d in DISCIPLINES)
    b = head_block("Contact Us — Meridian Engineering Consultancy",
                   "Contact MEC — Ehssan Street, Al Amerat, Muscat, Oman. Email info@meridianengconsultants.com or call +968 9700 4250.")
    b += header("contact.html")
    b += page_hero("Contact Us", "Start the Conversation.",
                   "Tell us about your project — feasibility, design, supervision or full programme management.",
                   "hero-home.jpg", "Construction site with engineers at dawn", "05 — CONTACT",
                   after_lede='''<p class="type-line" aria-hidden="true">Talk to us about&nbsp;<span class="type-word" data-typewriter data-words='["feasibility studies.","detailed engineering design.","construction supervision.","urban planning.","traffic impact studies."]'>feasibility studies.</span><span class="type-caret"></span></p>
        <noscript><p class="type-line">Talk to us about feasibility studies, detailed engineering design, construction supervision and more.</p></noscript>''')
    b += f'''<main id="top">
<section class="section">
  <div class="wrap">
    <div class="contact-layout">
      <div>
        <div class="section-head" data-reveal style="margin-bottom:30px;">
          <div>
            <p class="eyebrow">Enquiry Form</p>
            <h2 class="display-md">Send us your brief.</h2>
          </div>
        </div>
        <form id="contact-form" novalidate data-reveal>
          <div class="form-grid">
            <div class="field">
              <label for="cf-name">Full Name *</label>
              <input id="cf-name" name="name" type="text" autocomplete="name" required>
              <span class="field-error">Please enter your name.</span>
            </div>
            <div class="field">
              <label for="cf-email">Email *</label>
              <input id="cf-email" name="email" type="email" autocomplete="email" required>
              <span class="field-error">Please enter a valid email address.</span>
            </div>
            <div class="field">
              <label for="cf-phone">Phone</label>
              <input id="cf-phone" name="phone" type="tel" autocomplete="tel" placeholder="+968 …">
            </div>
            <div class="field">
              <label for="cf-company">Company / Organisation</label>
              <input id="cf-company" name="company" type="text" autocomplete="organization">
            </div>
            <div class="field field--full">
              <label for="cf-discipline">Related Discipline</label>
              <div class="select-wrap">
                <select id="cf-discipline" name="discipline">
                  <option value="">General enquiry</option>
{options}                </select>
              </div>
            </div>
            <div class="field field--full">
              <label for="cf-message">Message *</label>
              <textarea id="cf-message" name="message" required placeholder="Briefly describe your project, its location and the stage you are at."></textarea>
              <span class="field-error">Please enter a short message.</span>
            </div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;margin-top:26px;flex-wrap:wrap;">
            <button class="btn btn--solid" type="submit">Send Message<span class="arr">{ic("arrow","arr")}</span></button>
            <p class="form-note">Validates locally — form endpoint (Formspree/Web3Forms) connected at deployment.</p>
          </div>
        </form>
        <div class="form-success" id="form-success" role="status">
          {ic("check", "")}
          <div>
            <h3 style="margin-bottom:6px;">Thank you — message recorded.</h3>
            <p class="lede" style="font-size:15px;">Your enquiry has been validated successfully. Once the form endpoint is connected, submissions arrive directly at {EMAIL}. You can also reach us on {PHONE_DISPLAY} in the meantime.</p>
          </div>
        </div>
      </div>
      <div>
        <div class="cells" data-reveal data-reveal-stagger>
          <div class="cell info-cell" data-reveal-child>
            {ic("pin")}
            <div><h3>Muscat Office</h3><p>{ADDRESS}</p></div>
          </div>
          <div class="cell info-cell" data-reveal-child>
            {ic("mail")}
            <div><h3>Email</h3><p><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
          </div>
          <div class="cell info-cell" data-reveal-child>
            {ic("phone")}
            <div><h3>Phone</h3><p><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></p></div>
          </div>
          <div class="cell info-cell" data-reveal-child>
            {ic("clock")}
            <div><h3>Working Hours</h3><p><!-- PLACEHOLDER: confirm working hours with client -->Sunday – Thursday, 08:00 – 17:00 (Oman Time)</p></div>
          </div>
        </div>
        {socials_html()}
      </div>
    </div>
    <div class="map-frame" data-reveal>
      <!-- PLACEHOLDER MAP: replace q= with exact office coordinates when confirmed -->
      <iframe title="Map — Al Amerat, Muscat, Oman" src="https://www.google.com/maps?q=Al%20Amerat%2C%20Muscat%2C%20Oman&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
  </div>
</section>
</main>
''' + footer()
    return b

# ---------------------------------------------------------------- build ----
PAGES = {
    "index.html": page_home,
    "about.html": page_about,
    "services.html": page_services,
    "projects.html": page_projects,
    "disciplines.html": page_disciplines,
    "contact.html": page_contact,
}

def main():
    for fname, fn in PAGES.items():
        path = os.path.join(ROOT, fname)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("built", fname, os.path.getsize(path), "bytes")

if __name__ == "__main__":
    main()
