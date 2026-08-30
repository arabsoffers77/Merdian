/* ============================================================
   MEC — animation layer (GSAP 3.12 + ScrollTrigger, vendored)
   Spec: durations 600–900ms reveals · hero split 1000–1500ms ·
   hovers 200–400ms · stagger 80–120ms · ease-out entrances ·
   fire-once reveals · prefers-reduced-motion honored
   ============================================================ */
(function () {
  'use strict';

  var REDUCED = false;
  try { REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

  function forceVisibleAll() {
    /* safety net: nothing may stay hidden, ever */
    document.querySelectorAll('[data-reveal],[data-reveal-child]').forEach(function (el) {
      el.classList.add('is-in'); el.style.opacity = ''; el.style.transform = '';
    });
    var hm = document.querySelector('.hero-media');
    if (hm) { hm.style.width = ''; }
  }

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {

    /* ---------- header state ---------- */
    var header = document.querySelector('.site-header');
    function onScrollHeader() {
      if (!header) return;
      header.classList.toggle('is-scrolled', (window.scrollY || 0) > 24);
    }
    onScrollHeader();
    window.addEventListener('scroll', onScrollHeader, { passive: true });

    /* ---------- mobile nav ---------- */
    var toggle = document.querySelector('.nav-toggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var open = document.body.classList.toggle('nav-open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      document.querySelectorAll('.main-nav a').forEach(function (a) {
        a.addEventListener('click', function () {
          document.body.classList.remove('nav-open');
          if (toggle) toggle.setAttribute('aria-expanded', 'false');
        });
      });
    }

    /* ============================================================
       PROJECT DETAILS MODAL — cards open it via data-* attributes
       ============================================================ */
    var pmodal = document.getElementById('project-modal');
    if (pmodal) {
      var pmImg = document.getElementById('pm-img');
      var pmName = document.getElementById('pm-name');
      var pmClient = document.getElementById('pm-client');
      var pmCat = document.getElementById('pm-cat');
      var pmDesc = document.getElementById('pm-desc');

      function openPmodal(card) {
        if (!card) return;
        var imgEl = card.querySelector('.proj-media img');
        if (pmImg && imgEl) {
          pmImg.src = imgEl.currentSrc || imgEl.src;
          pmImg.alt = imgEl.alt || '';
        }
        if (pmName) pmName.textContent = card.getAttribute('data-name') || '';
        if (pmClient) pmClient.textContent = card.getAttribute('data-client') || '';
        if (pmCat) pmCat.textContent = card.getAttribute('data-cat-label') || '';
        if (pmDesc) pmDesc.textContent = card.getAttribute('data-desc') || '';
        pmodal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
      }
      function closePmodal() {
        pmodal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
      }

      document.querySelectorAll('.proj-card').forEach(function (card) {
        card.addEventListener('click', function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          openPmodal(card);
        });
      });
      pmodal.querySelectorAll('[data-pmodal-close]').forEach(function (el) {
        el.addEventListener('click', closePmodal);
      });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' && pmodal.getAttribute('aria-hidden') === 'false') {
          closePmodal();
        }
      });
      window.addEventListener('pageshow', function () { closePmodal(); });
    }

    /* ============================================================
       3D FLIP CARDS — tap toggles (mobile), Enter/Space toggle,
       aria-pressed kept in sync for assistive tech
       ============================================================ */
    document.querySelectorAll('.flip-card').forEach(function (card) {
      card.addEventListener('click', function () {
        var flipped = card.classList.toggle('is-flipped');
        card.setAttribute('aria-pressed', flipped ? 'true' : 'false');
      });
      card.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ' || ev.key === 'Spacebar') {
          ev.preventDefault();
          var flipped2 = card.classList.toggle('is-flipped');
          card.setAttribute('aria-pressed', flipped2 ? 'true' : 'false');
        }
      });
    });

    /* ============================================================
       TIMELINE — responsive wrapping grid; nothing to manage at runtime
       ============================================================ */

    /* ============================================================
       SCROLL-TEXT VALUES — giant words light up as they cross
       the viewport midline (page scroll drives it; no scroll-jacking)
       ============================================================ */
    var stBox = document.querySelector('[data-scrolltext]');
    if (stBox && 'IntersectionObserver' in window) {
      var stItems = Array.prototype.slice.call(stBox.querySelectorAll('.st-item'));
      var stCurrent = 0;
      var stIo = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var idx = stItems.indexOf(en.target);
          if (idx !== -1 && idx !== stCurrent) {
            stItems[stCurrent].classList.remove('is-active');
            en.target.classList.add('is-active');
            stCurrent = idx;
          }
        });
      }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
      stItems.forEach(function (it) { stIo.observe(it); });
      /* keep last item lit once its row has passed upward past the band */
      window.addEventListener('scroll', function () {
        var rect = stBox.getBoundingClientRect();
        var mid = window.innerHeight / 2;
        if (rect.bottom < mid && stCurrent !== stItems.length - 1) {
          stItems[stCurrent].classList.remove('is-active');
          stItems[stItems.length - 1].classList.add('is-active');
          stCurrent = stItems.length - 1;
        }
      }, { passive: true });
    }

    /* ============================================================
       TYPEWRITER (contact hero) — natural variance, loops forever;
       fixed single line: a word that would overflow is never started —
       typing flips to delete as the caret nears the line edge
       ============================================================ */
    var typeEl = document.querySelector('[data-typewriter]');
    if (typeEl) {
      var tWords = [];
      try { tWords = JSON.parse(typeEl.getAttribute('data-words')) || []; } catch (e) {}
      if (!tWords.length) tWords = [typeEl.textContent || ''];
      var tIdx = 0, tPos = tWords[0].length, tDeleting = false;
      var PREFIX = 'Talk to us about';   /* keep in sync with markup */

      function fitCheck() {
        /* will the FULL current word + prefix + caret fit on the line? */
        var line = typeEl.closest('.type-line');
        if (!line) return true;
        var probe = document.createElement('span');
        probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;';
        probe.style.font = getComputedStyle(typeEl).font;
        probe.textContent = PREFIX + '\u00A0' + tWords[tIdx];
        line.appendChild(probe);
        var w = probe.getBoundingClientRect().width;
        line.removeChild(probe);
        return w <= line.clientWidth - Math.round(parseFloat(getComputedStyle(typeEl).fontSize) * 0.6);   /* caret + safety */
      }
      function tDelay(kind, base) {
        if (REDUCED) return kind === 'hold' ? 1600 : 500;
        if (kind === 'type') {
          var r = Math.random();                       /* human-ish rhythm */
          if (r < 0.1) return base * 2;                /* hesitation */
          if (r > 0.9) return base * 0.5;              /* burst */
          return base * (0.6 + Math.random() * 0.8);
        }
        return base;
      }
      function tickType() {
        if (tDeleting) {
          tPos -= 1;
        } else {
          tPos += 1;
          if (!fitCheck() && !tDeleting) {             /* won't fit → delete now */
            tPos -= 1;
            tDeleting = true;
            setTimeout(tickType, tDelay('type', 34));
            return;
          }
        }
        typeEl.textContent = tWords[tIdx].slice(0, Math.max(tPos, 0));
        if (!tDeleting && tPos >= tWords[tIdx].length) {
          setTimeout(function () { tDeleting = true; tickType(); }, tDelay('hold', REDUCED ? 1400 : 2100));
        } else if (tDeleting && tPos <= 0) {
          tDeleting = false;
          tIdx = (tIdx + 1) % tWords.length;
          setTimeout(tickType, tDelay('gap', REDUCED ? 350 : 650));
        } else {
          setTimeout(tickType, tDelay('type', tDeleting ? 34 : 52));
        }
      }
      if (REDUCED) {
        /* reduced motion: show only words that fit whole, swap calmly */
        setInterval(function () {
          for (var tries = 0; tries < tWords.length; tries++) {
            tIdx = (tIdx + 1) % tWords.length;
            tPos = tWords[tIdx].length;
            typeEl.textContent = tWords[tIdx];
            if (fitCheck()) break;
            typeEl.textContent = '';
          }
        }, 2600);
      } else {
        setTimeout(tickType, 900);
      }
    }

    /* ============================================================
       ASSOC FLASH (about) — continents cycle on their own line,
       below the paragraph (never inline, never disturbs the text)
       ============================================================ */
    var assoc = document.querySelector('[data-assoc]');
    if (assoc) {
      var aWords = ['Europe', 'USA', 'Asia', 'Africa'];
      var aWord = assoc.querySelector('.afw');
      var ai = 0;
      function aNext() {
        ai = (ai + 1) % aWords.length;
        aWord.classList.add('is-out');
        setTimeout(function () {
          aWord.textContent = aWords[ai];
          aWord.classList.remove('is-out');
          aWord.classList.add('is-in');
          setTimeout(function () { aWord.classList.remove('is-in'); }, 240);
        }, 160);
      }
      setInterval(aNext, REDUCED ? 2400 : 1900);
      /* start only when scrolled into view */
      if ('IntersectionObserver' in window) {
        var aIo = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) { if (en.isIntersecting) aIo.disconnect(); });
        }, { threshold: 0.4 });
        aIo.observe(assoc);
      }
    }

    /* ============================================================
       CHROMA SPOTLIGHT (Selected Work) — pointer-following radial
       light per card; adds glow near the cursor, never hides content.
       CONTENT-FIRST: the grid is always visible in markup/CSS; the
       entrance is an additive fade-in from a VISIBLE baseline
       (gsap.from), so any failure leaves content shown, never blank.
       ============================================================ */
    var featGrid = document.querySelector('.feat-grid');
    if (featGrid && ST) {
      gsap.from(featGrid, {
        opacity: 0, y: 24, duration: .8, ease: 'power2.out',
        clearProps: 'opacity,transform',
        scrollTrigger: { trigger: featGrid,
          start: function () {
            var top = featGrid.getBoundingClientRect().top +
                      (window.pageYOffset || 0);
            return Math.max(0, Math.min(top - window.innerHeight * 0.9,
                     ScrollTrigger.maxScroll(window) - 2));
          }, once: true }
      });
    }
    if (!REDUCED && window.matchMedia && matchMedia('(hover:hover)').matches) {
      document.querySelectorAll('.chroma-card').forEach(function (card) {
        card.addEventListener('pointermove', function (e) {
          var r = card.getBoundingClientRect();
          card.style.setProperty('--mx', Math.round(e.clientX - r.left) + 'px');
          card.style.setProperty('--my', Math.round(e.clientY - r.top) + 'px');
        }, { passive: true });
      });

      /* ---- chroma lens: damped colour-reveal following the cursor ---- */
      (function () {
        var grid = document.querySelector('.feat-grid');
        if (!grid) return;
        var test = document.createElement('div');
        test.style.cssText = 'backdrop-filter:grayscale(1)';
        if (!('backdropFilter' in test.style) && !('webkitBackdropFilter' in test.style)) return;
        var lens = document.createElement('div'); lens.className = 'chroma-lens';
        var idle = document.createElement('div'); idle.className = 'chroma-idle';
        grid.appendChild(lens); grid.appendChild(idle);
        var px = 0, py = 0, tx = null, ty = null, tween = null;
        function setVars(x, y) {
          lens.style.setProperty('--lx', Math.round(x) + 'px');
          lens.style.setProperty('--ly', Math.round(y) + 'px');
        }
        grid.addEventListener('pointermove', function (e) {
          var r = grid.getBoundingClientRect();
          tx = e.clientX - r.left; ty = e.clientY - r.top;
          if (tween) { tween.kill(); tween = null; }
          px = tx; py = ty;                 /* damping via gsap.to below */
          gsap.to({ x: px, y: py }, {
            x: tx, y: ty, duration: .45, ease: 'power3.out',
            onUpdate: function () {
              setVars(this.targets()[0].x, this.targets()[0].y);
            }
          });
          idle.style.opacity = '0';
        }, { passive: true });
        grid.addEventListener('pointerleave', function () {
          idle.style.opacity = '1';         /* fade the dimmer back in */
        });
      })();
    }

    /* ---------- footer year ---------- */
    document.querySelectorAll('[data-year]').forEach(function (el) {
      el.textContent = String(new Date().getFullYear());
    });

    /* ---------- no-GSAP / reduced-motion exit path ---------- */
    /* NOTE: in GSAP 3 the global `gsap` is an OBJECT (not a function) */
    var hasGSAP = !!(window.gsap && typeof window.gsap.to === 'function');
    if (REDUCED || !hasGSAP) {
      if (hasGSAP && window.ScrollTrigger) { try { window.gsap.registerPlugin(window.ScrollTrigger); } catch (e) {} }
      forceVisibleAll();
      initRowsNoAnim(); initFilters(true); initForm(); initPageFade(!REDUCED && false);
      return;
    }

    var gsap = window.gsap;
    try { gsap.registerPlugin(window.ScrollTrigger); } catch (e) {}
    var ST = window.ScrollTrigger;

    /* ============================================================
       HERO ENTRANCE — absolute timeline positions only
       (long ambient tweens never chained relatively — see skill note)
       ============================================================ */
    function splitWords(el) {
      if (!el || el.dataset.split === 'done') return [];
      var text = el.textContent;
      var parts = text.split(/\s+/);
      el.textContent = '';
      var spans = parts.map(function (w, i) {
        var s = document.createElement('span');
        s.className = 'split-word';
        s.textContent = w;
        el.appendChild(s);
        if (i < parts.length - 1) el.appendChild(document.createTextNode(' '));
        return s;
      });
      el.dataset.split = 'done';
      return spans;
    }

    var titleEl = document.querySelector('.hero-title');
    if (titleEl) {
      var words = splitWords(titleEl);
      var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
      tl.fromTo(words,
        { yPercent: 115, opacity: 0 },
        { yPercent: 0, opacity: 1, duration: 1.15, stagger: 0.07 }, 0);          /* words: 1000–1500ms band */
      var eb = document.querySelector('.hero .eyebrow');
      if (eb) tl.fromTo(eb, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: .7 }, 0.05);
      var sub = document.querySelector('.hero-sub');
      if (sub) tl.fromTo(sub, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .8 }, 0.5);
      var ctas = document.querySelectorAll('.hero-ctas .btn');
      if (ctas.length) tl.fromTo(ctas, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .7, stagger: 0.09 }, 0.65);
      var cue = document.querySelector('.scroll-cue');
      if (cue) tl.fromTo(cue, { opacity: 0 }, { opacity: 1, duration: .6 }, 0.9);
    } else {
      /* inner pages: simple page-hero entrance */
      var phEls = document.querySelectorAll('.page-hero-copy > *');
      if (phEls.length) {
        gsap.fromTo(phEls, { opacity: 0, y: 22 },
          { opacity: 1, y: 0, duration: .8, ease: 'power2.out', stagger: 0.09 });
      }
    }

    /* ---------- CTA heading — 3D scroll-triggered word reveal ---------- */
    var ctaTitle = document.querySelector('.cta-band h2');
    if (ctaTitle && ST) {
      var ctaWords = splitWords(ctaTitle);
      if (ctaWords.length) {
        gsap.fromTo(ctaWords,
          { rotateX: -75, y: 26, opacity: 0, transformOrigin: '50% 100%' },
          {
            rotateX: 0, y: 0, opacity: 1, duration: .85, stagger: 0.08, ease: 'power3.out',
            scrollTrigger: { trigger: ctaTitle, start: 'top 88%', once: true }
          });
      }
    }

    /* ---------- Ken Burns (standalone ambient tween, not chained) ---------- */
    var kbImg = document.querySelector('.hero-media img, .hero-video video, .page-hero-media img');
    if (kbImg) gsap.to(kbImg, { scale: 1.08, duration: 18, ease: 'none', repeat: -1, yoyo: true });

    /* ---------- scroll-expansion hero media (§4 pattern) ---------- */
    var heroMedia = document.querySelector('.hero-media');
    if (heroMedia && ST) {
      gsap.fromTo(heroMedia,
        { width: '74%', borderRadius: '18px' },
        {
          width: '100%', borderRadius: '10px', ease: 'none',
          scrollTrigger: { trigger: heroMedia, start: 'top 82%', end: 'top 18%', scrub: 0.4 }
        });
    }

    /* ============================================================
       SCROLL REVEALS — once:true, threshold ~ top 86%
       ============================================================ */
    /* Reveal targets: skip containers double-gated by an ancestor */
    var revealEls = Array.prototype.filter.call(
      document.querySelectorAll('[data-reveal]'),
      function (el) {
        var a = el.parentElement;
        while (a && a !== document.body) {
          if (a.hasAttribute && a.hasAttribute('data-reveal')) return false;
          a = a.parentElement;
        }
        return true;
      }
    );

    /* Function-based start: re-evaluated on EVERY ScrollTrigger refresh
       (resize, load, late images) and CLAMPED into the reachable scroll
       range — a reveal point can never sit past max-scroll again, so no
       section can stay hidden on short viewports. */
    function clampedStart(el) {
      return function () {
        var top = el.getBoundingClientRect().top +
                  (window.pageYOffset || document.documentElement.scrollTop || 0);
        var ideal = top - window.innerHeight * 0.86;
        var max = ScrollTrigger.maxScroll(window);
        return Math.max(0, Math.min(ideal, max - 2));
      };
    }

    /* safety net: any [data-reveal-child] not reached by an animated parent
       reveals itself independently */
    Array.prototype.forEach.call(
      document.querySelectorAll('[data-reveal]'),
      function (el) { el.__mecKids = el.querySelectorAll(':scope > [data-reveal-child]').length; }
    );
    Array.prototype.forEach.call(document.querySelectorAll('[data-reveal-child]'), function (kid) {
      var p = kid.closest('[data-reveal]');
      if (!p || p.__mecKids === 0) {
        gsap.fromTo(kid, { opacity: 0, y: 26 },
          {
            opacity: 1, y: 0, duration: .7, ease: 'power2.out',
            scrollTrigger: { trigger: kid, start: 'top 90%', once: true },
            onStart: function () { kid.classList.add('is-in'); }
          });
      }
    });

    revealEls.forEach(function (el) {
      var kids = el.querySelectorAll(':scope > [data-reveal-child]');
      var stCfg = { trigger: el, start: clampedStart(el), once: true };
      if (el.hasAttribute('data-reveal-stagger') && kids.length) {
        gsap.fromTo(kids, { opacity: 0, y: 30 },
          {
            opacity: 1, y: 0, duration: .8, ease: 'power2.out', stagger: 0.1,
            scrollTrigger: stCfg,
            onStart: function () { el.classList.add('is-in'); }
          });
        kids.forEach(function (k) {
          k.classList.add('is-in');               /* CSS gate satisfied by tween target state */
        });
      } else {
        gsap.fromTo(el, { opacity: 0, y: 28 },
          {
            opacity: 1, y: 0, duration: .8, ease: 'power2.out',
            scrollTrigger: stCfg,
            onStart: function () { el.classList.add('is-in'); }
          });
      }
    });

    /* ---------- stat counters (About page) ---------- */
    document.querySelectorAll('[data-count]').forEach(function (el) {
      var target = parseInt(el.getAttribute('data-count'), 10) || 0;
      var numSpan = el.querySelector('.stat-num-val') || el;
      var obj = { v: 0 };
      gsap.to(obj, {
        v: target, duration: 1.6, ease: 'power2.out',
        scrollTrigger: { trigger: el, start: 'top 87%', once: true },
        onUpdate: function () { numSpan.textContent = Math.round(obj.v).toLocaleString('en-US'); }
      });
    });

    /* ============================================================
       EXPANDABLE ROWS (Services / Disciplines) — 300ms height+fade
       ============================================================ */
    function bindRow(row) {
      var btn = row.querySelector('.xrow-btn');
      var panel = row.querySelector('.xrow-panel');
      if (!btn || !panel) return;
      btn.setAttribute('aria-expanded', 'false');
      btn.addEventListener('click', function () {
        var open = row.classList.toggle('is-open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        gsap.to(panel, {
          height: open ? 'auto' : 0,
          opacity: open ? 1 : 0,
          duration: 0.3, ease: 'power1.inOut',
          onComplete: function () { if (ST && open) ST.refresh(); }
        });
      });
    }
    document.querySelectorAll('.xrow').forEach(bindRow);

    function initRowsNoAnim() { /* fallback: rows toggle instantly */
      document.querySelectorAll('.xrow').forEach(function (row) {
        var btn = row.querySelector('.xrow-btn'), panel = row.querySelector('.xrow-panel');
        if (!btn || !panel) return;
        btn.setAttribute('aria-expanded', 'false');
        btn.addEventListener('click', function () {
          var open = row.classList.toggle('is-open');
          btn.setAttribute('aria-expanded', open ? 'true' : 'false');
          panel.style.height = open ? 'auto' : '0px';
          panel.style.opacity = open ? '1' : '0';
        });
      });
    }

    /* ============================================================
       PROJECT FILTERS (Projects page)
       ============================================================ */
    function initFilters(instant) {
      var bar = document.querySelector('.filters');
      if (!bar) return;
      var chips = bar.querySelectorAll('.chip');
      var cards = Array.prototype.slice.call(document.querySelectorAll('[data-category]'));
      if (!chips.length || !cards.length) return;
      chips.forEach(function (chip) {
        chip.addEventListener('click', function () {
          chips.forEach(function (c) { c.classList.remove('is-active'); });
          chip.classList.add('is-active');
          var f = chip.getAttribute('data-filter');
          cards.forEach(function (card) {
            var show = (f === '*' ) || (card.getAttribute('data-category') || '').split(' ').indexOf(f) !== -1;
            card.hidden = !show;
          });
          var vis = cards.filter(function (c) { return !c.hidden; });
          if (!instant && window.gsap) {
            window.gsap.fromTo(vis, { opacity: 0, y: 16 },
              { opacity: 1, y: 0, duration: .45, ease: 'power2.out', stagger: 0.06, clearProps: 'transform' });
          }
          if (window.ScrollTrigger) window.ScrollTrigger.refresh();
        });
      });
    }
    initFilters(false);

    /* ============================================================
       CONTACT FORM — validate-only (endpoint wired later)
       ============================================================ */
    function initForm() {
      var form = document.getElementById('contact-form');
      if (!form) return;
      var success = document.getElementById('form-success');
      var emailRx = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

      form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        var ok = true;
        form.querySelectorAll('[required]').forEach(function (input) {
          var field = input.closest('.field');
          var val = (input.value || '').trim();
          var bad = !val ||
            (input.type === 'email' && !emailRx.test(val));
          if (bad) ok = false;
          if (field) field.classList.toggle('has-error', bad);
          input.classList.toggle('is-invalid', bad);
        });
        if (!ok) return;
        form.style.display = 'none';
        if (success) {
          success.classList.add('is-visible');
          if (window.gsap) window.gsap.from(success, { opacity: 0, y: 16, duration: .5, ease: 'power2.out' });
        }
      });

      form.querySelectorAll('[required]').forEach(function (input) {
        input.addEventListener('input', function () {
          input.classList.remove('is-invalid');
          var f = input.closest('.field'); if (f) f.classList.remove('has-error');
        });
      });
    }
    initForm();

    /* ============================================================
       PAGE TRANSITIONS — soft 260ms fade between internal pages
       ============================================================ */
    function initPageFade(enabled) {
      if (!enabled) return;
      var overlay = document.createElement('div');
      overlay.style.cssText =
        'position:fixed;inset:0;background:#fff;z-index:90;pointer-events:none;opacity:0;' +
        'transition:opacity 260ms cubic-bezier(.22,.61,.36,1)';
      document.body.appendChild(overlay);

      window.addEventListener('pageshow', function (ev) {
        overlay.style.opacity = '0';
        if (ev.persisted) forceVisibleAll();
      });

      document.addEventListener('click', function (ev) {
        if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
        var a = ev.target.closest ? ev.target.closest('a[href]') : null;
        if (!a || a.target === '_blank') return;
        var href = a.getAttribute('href') || '';
        if (!/\.html(#.*)?$/.test(href) || /^https?:/i.test(a.href) === false) {
          if (!/^https?:/i.test(a.href)) return;         /* only http(s) links */
        }
        var dest = new URL(a.href, location.href);
        if (dest.origin !== location.origin) return;
        if (!/\.html$/.test(dest.pathname)) return;
        ev.preventDefault();
        overlay.style.opacity = '1';
        setTimeout(function () { location.href = dest.href; }, 270);
      });
    }
    initPageFade(true);

    window.addEventListener('load', function () { if (ST) ST.refresh(); });
  });
})();
