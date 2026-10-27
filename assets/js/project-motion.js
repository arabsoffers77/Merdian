/* Pointer position is time: left = first frame, centre = midpoint, right = last.
   Paused short-GOP films, one active decoder, coalesced seeks; no reverse play.
   Images remain the baseline. Touch/reduced-motion/save-data open normal films. */
(function () {
  'use strict';
  var cards = Array.from(document.querySelectorAll('.proj-card[data-scrub]'));
  if (!cards.length) return;
  var fine = matchMedia('(hover: hover) and (pointer: fine)');
  var reduced = matchMedia('(prefers-reduced-motion: reduce)');
  var ar = document.documentElement.lang === 'ar';
  var active = null, raf = 0, warm = [], states = new WeakMap();
  function permitted() { return fine.matches && !reduced.matches && !(navigator.connection || {}).saveData; }
  function stop() {
    cancelAnimationFrame(raf); raf = 0;
    if (!active) return;
    active.card.classList.remove('is-scrubbing', 'is-scrub-ready');
    active.video.pause(); active = null;
  }
  function schedule() { if (!raf && active && !document.hidden) raf = requestAnimationFrame(seek); }
  function seek() {
    raf = 0;
    var state = active;
    if (!state || !permitted() || document.hidden) return stop();
    var video = state.video;
    if (video.readyState < 1 || video.seeking) return;
    var end = Math.max(0, video.duration - 1 / state.fps);
    var target = state.progress * end, delta = target - video.currentTime;
    if (Math.abs(delta) < .018) return;
    // A single outstanding seek; new pointer events replace the target.
    var next = Math.abs(delta) < .08 ? target : video.currentTime + delta * .42;
    try { video.currentTime = Math.max(0, Math.min(end, next)); }
    catch (_) { stop(); }
  }
  function retain(state) {
    warm = warm.filter(function (s) { return s !== state; }); warm.push(state);
    while (warm.length > 3) {
      var old = warm.shift();
      old.video.removeAttribute('src'); old.video.load(); old.loaded = false;
      old.card.dataset.scrubState = 'idle';
    }
  }
  function begin(state) {
    if (!permitted() || state.failed) return;
    if (active === state) return;
    stop(); active = state; state.progress = .5;
    state.card.classList.add('is-scrubbing');
    state.card.style.setProperty('--scrub-progress', '.5');
    retain(state);
    if (!state.loaded) {
      state.card.dataset.scrubState = 'loading';
      state.loaded = true; state.video.src = state.card.dataset.scrub;
      state.video.preload = 'auto'; state.video.load();
    } else if (state.video.readyState >= 1 && isFinite(state.video.duration)) {
      state.video.currentTime = Math.max(0, state.video.duration / 2);
    }
    schedule();
  }
  cards.forEach(function (card) {
    var video = card.querySelector('.project-scrub-video'), media = card.querySelector('.proj-media');
    if (!video || !media) return;
    var state = {card:card,video:video,progress:.5,loaded:false,failed:false,fps:Number(card.dataset.scrubFps) || 24};
    states.set(card,state); video.muted = true;
    video.addEventListener('loadedmetadata', function () {
      if (!video.hasAttribute('src') || !isFinite(video.duration)) return;
      video.currentTime = Math.max(0, video.duration / 2);
    });
    video.addEventListener('seeked', function () {
      if (active !== state || !video.hasAttribute('src')) return;
      state.card.dataset.scrubState = 'ready'; state.card.classList.add('is-scrub-ready');
      state.card.style.setProperty('--scrub-progress', String(video.currentTime / Math.max(.1,video.duration)));
      schedule();
    });
    video.addEventListener('error', function () {
      if (!video.hasAttribute('src')) return;
      state.failed = true; card.dataset.scrubState = 'error';
      if (active === state) stop();
    });
    card.addEventListener('pointerenter', function (e) { if (e.pointerType !== 'touch') begin(state); });
    card.addEventListener('pointermove', function (e) {
      if (e.pointerType === 'touch' || !permitted()) return;
      begin(state); if (active !== state) return;
      var rect = media.getBoundingClientRect();
      state.progress = Math.max(0, Math.min(1, (e.clientX - rect.left) / Math.max(1, rect.width)));
      schedule();
    });
    card.addEventListener('pointerleave', function () { if (active === state) stop(); });
    card.addEventListener('focus', function () { begin(state); });
    card.addEventListener('blur', function () { if (active === state) stop(); });
    card.addEventListener('keydown', function (e) {
      if (!permitted() || !['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;
      e.preventDefault(); e.stopImmediatePropagation(); begin(state);
      if (active !== state) return;
      state.progress = e.key === 'Home' ? 0 : e.key === 'End' ? 1 : Math.max(0,Math.min(1,state.progress + (e.key === 'ArrowRight' ? .1 : -.1)));
      schedule();
    });
    if (permitted()) {
      card.classList.add('project-scrub-enabled');
      var label = card.querySelector('.proj-film-mark span');
      if (label) label.textContent = ar ? 'حرّك المؤشر لاستكشاف المشهد' : 'Move to explore the film';
    }
  });
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (!e.isIntersecting && active && active.card === e.target) stop(); });
    }); cards.forEach(function (card) { observer.observe(card); });
  }
  document.addEventListener('visibilitychange', function () { if (document.hidden) stop(); });
  document.addEventListener('project:modalopen', stop);
  document.addEventListener('project:filter', stop);
  window.addEventListener('pagehide', stop);
  function preferenceChanged() {
    stop(); cards.forEach(function (card) { card.classList.toggle('project-scrub-enabled',permitted()); });
  }
  if (fine.addEventListener) fine.addEventListener('change',preferenceChanged);
  if (reduced.addEventListener) reduced.addEventListener('change',preferenceChanged);
})();
