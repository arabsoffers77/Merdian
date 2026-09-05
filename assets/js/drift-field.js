/* ---------- Drift Field — pinned depth-scroll photo field (home, About) ----------
   See assets/css/style.css .about-drift-section / .drift-field blocks for the
   full design rationale. Grid of hexagon-clipped tiles at 3 depth layers,
   positions modulo-wrapped so panning never runs out of images. Auto-drifts on
   its own timer; drag for direct control with the same ease-then-momentum model
   as the associations globe (assets/js/globe.js).

   Desktop only: the section pins for a short scroll distance (GSAP
   ScrollTrigger, vendored) and that scroll drives a depth-axis camera flythrough
   — nearer layers rush past faster while far layers barely move, giving a true
   parallax depth illusion — then un-pins and the page continues normally.
   Mobile and prefers-reduced-motion skip the pin entirely (ambient drift + drag
   only); pin is deliberately desktop-only, matching common scroll-jacking
   practice, since pin can fight browser chrome on touch.

   Click any tile and the camera flies TOWARD it along the Z-axis (depth);
   the about-copy panel fades out smoothly during the approach. Click again
   (or the background) to reverse. */
(function () {
  var field = document.getElementById('about-drift');
  var section = document.getElementById('about-drift-section');
  if (!field || !section) return;

  var REDUCED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  var IMAGES = [
    'assets/img/proj-salalah.jpg',
    'assets/img/proj-albahjal.jpg',
    'assets/img/proj-awqad.jpg',
    'assets/img/proj-redan.jpg',
    'assets/img/proj-alsalam.jpg',
    'assets/img/proj-restaurant.jpg',
    'assets/img/about-story.jpg',
    'assets/img/hero-projects.jpg',
    'assets/img/hero-about.jpg'
  ];

  /* Three depth layers — the 'depth' value (0..1) drives per-layer parallax:
     layer 0 = far background, layer 2 = near foreground */
  var LAYERS = [
    { size: 54, opacity: .38, speed: .55, depth: 0.0 },
    { size: 76, opacity: .70, speed: .90, depth: 0.5 },
    { size: 104, opacity: .98, speed: 1.30, depth: 1.0 }
  ];

  var cellSize = 128;
  var cols = 0, rows = 0, totalW = 0, totalH = 0;
  var containerW = 0, containerH = 0;
  var tiles = [];

  // About-copy panel element (text card)
  var aboutPanel = section ? section.querySelector('.about-copy--panel') : null;

  // Seeded pseudo-random so the layout is stable across rebuilds/resizes
  function rand(seed) {
    var x = Math.sin(seed * 12.9898) * 43758.5453;
    return x - Math.floor(x);
  }

  function build() {
    var rect = field.getBoundingClientRect();
    containerW = rect.width;
    containerH = rect.height;
    cellSize = Math.max(120, Math.min(190, containerW / 5.4));
    cols = Math.ceil(containerW / cellSize) + 5;
    rows = Math.ceil(containerH / cellSize) + 5;
    totalW = cols * cellSize;
    totalH = rows * cellSize;

    field.querySelectorAll('.drift-tile').forEach(function (el) { el.remove(); });
    tiles = [];

    for (var c = 0; c < cols; c++) {
      for (var r = 0; r < rows; r++) {
        var seed = c * 41 + r * 23 + 7;
        var layer = LAYERS[Math.floor(rand(seed) * LAYERS.length)];
        var img = IMAGES[Math.floor(rand(seed * 5.3) * IMAGES.length)];
        var el = document.createElement('div');
        el.className = 'drift-tile';
        var size = layer.size * (containerW < 560 ? 0.72 : 1);
        el.style.width = size + 'px';
        el.style.height = (size * 1.15) + 'px';
        var im = document.createElement('img');
        im.src = img;
        im.loading = 'lazy';
        im.alt = '';
        el.appendChild(im);
        field.appendChild(el);

        tiles.push({
          el: el,
          baseX: c * cellSize + (r % 2 ? cellSize / 2 : 0),
          baseY: r * cellSize,
          jitterX: (rand(seed * 3) - 0.5) * cellSize * 0.3,
          jitterY: (rand(seed * 4) - 0.5) * cellSize * 0.3,
          layer: layer,
          halfW: size / 2,
          halfH: (size * 1.15) / 2,
          focused: false
        });
      }
    }
  }

  function wrapMod(v, m) {
    return ((v % m) + m) % m;
  }

  var panX = 0, panY = 0;
  var dragTargetX = 0, dragTargetY = 0;
  var velX = 0, velY = 0;
  var pointerDown = false;
  var startX = 0, startY = 0;
  var dragStartPanX = 0, dragStartPanY = 0;
  var lastX = 0, lastY = 0, lastMoveTime = 0;
  var driftVX = 0.11, driftVY = 0.045;

  /* Scroll-driven depth camera — moves THROUGH the field along Z-axis.
     depthProgress 0→1 as user scrolls through the pinned section. */
  var depthProgress = 0;

  /* Click-to-fly: camera flies TOWARD the clicked tile along the Z-axis.
     Instead of growing the clicked tile, we simulate CAMERA MOVEMENT:
     — pick the clicked tile's screen position as the vanishing point
     — every frame, push ALL tiles outward from that vanishing point
       (closer tiles fly past faster, far tiles drift slowly = parallax)
     — all tiles scale up uniformly (camera approaching = everything grows)
     — the clicked tile, being right at the vanishing point, barely moves
       while everything else rushes outward past the viewer.              */
  var focusedTile = null;
  var focusAnim = 0;            // 0→1 smooth animation progress
  // Vanishing point: the screen-space XY the camera is flying toward
  var vpX = 0, vpY = 0;
  // Offset to smoothly slide the VP (and scene) to screen center
  var focusCenterDX = 0, focusCenterDY = 0;

  /* ---- Smooth panel visibility ---- */
  function updatePanelVisibility() {
    if (!aboutPanel) return;
    if (focusedTile && focusAnim > 0.05) {
      aboutPanel.style.opacity = Math.max(0, 1 - focusAnim * 1.4).toFixed(3);
      aboutPanel.style.transform = 'scale(' + (1 - focusAnim * 0.08).toFixed(3) + ') translateY(' + (focusAnim * 20).toFixed(1) + 'px)';
      aboutPanel.style.pointerEvents = 'none';
    } else {
      aboutPanel.style.opacity = '1';
      aboutPanel.style.transform = 'scale(1) translateY(0)';
      aboutPanel.style.pointerEvents = '';
    }
  }

  function render() {
    var cx = containerW / 2;
    var cy = containerH / 2;
    var maxDist = Math.sqrt(cx * cx + cy * cy);

    // Camera Z-zoom from focus click (uniform for all tiles)
    // Keep subtle so the focused tile stays within frame
    var camZoom = 1 + focusAnim * 0.8;

    for (var t = 0; t < tiles.length; t++) {
      var tile = tiles[t];
      var layerDepth = tile.layer.depth; // 0 = far, 1 = near

      // Base position with pan
      var x = wrapMod(tile.baseX + panX * tile.layer.speed + tile.jitterX, totalW) - totalW / 2 + cx;
      var y = wrapMod(tile.baseY + panY * tile.layer.speed + tile.jitterY, totalH) - totalH / 2 + cy;

      /* ---------- DEPTH CAMERA (scroll-driven) ---------- */
      var depthScale = 1 + depthProgress * (0.4 + layerDepth * 2.2);
      var pushFactor = depthProgress * (0.3 + layerDepth * 1.8);
      var ddx = (x - cx) * pushFactor;
      var ddy = (y - cy) * pushFactor;
      x += ddx;
      y += ddy;

      /* ---------- CLICK FOCUS: true camera Z-movement ----------
         The camera flies toward the vanishing point (vpX, vpY).
         Every tile is pushed OUTWARD from the VP — this is exactly what
         happens optically when a camera dollies forward: objects radiate
         from the aim point. The amount of push scales with focusAnim
         (how far the camera has traveled) and the tile's depth layer
         (near tiles rush past faster = parallax).                      */
      var scale = depthScale;
      var op = tile.layer.opacity;

      if (focusAnim > 0.001) {
        // The effective vanishing point slides toward screen center as anim progresses
        var effVPx = vpX + focusCenterDX * focusAnim;
        var effVPy = vpY + focusCenterDY * focusAnim;

        // Shift every tile by the centering offset so the scene pans
        x += focusCenterDX * focusAnim;
        y += focusCenterDY * focusAnim;

        // Vector from effective VP to this tile
        var fromVPx = x - effVPx;
        var fromVPy = y - effVPy;

        // Push outward from VP — depth-dependent parallax
        // Keep gentle so tiles don't fly off screen
        var layerPush = 0.5 + layerDepth * 1.2;
        var pushAmount = focusAnim * layerPush;
        x = effVPx + fromVPx * (1 + pushAmount);
        y = effVPy + fromVPy * (1 + pushAmount);

        // Uniform camera zoom — everything scales up as camera approaches
        scale = depthScale * camZoom;

        // Distance from VP determines opacity
        var distFromVP = Math.sqrt(fromVPx * fromVPx + fromVPy * fromVPy);
        var vpFade = Math.min(1, distFromVP / (maxDist * 0.4));
        op *= (1 - focusAnim * vpFade * 0.85);

        // Tiles that have flown off-screen fade fully
        if (x < -200 || x > containerW + 200 || y < -200 || y > containerH + 200) {
          op *= Math.max(0, 1 - focusAnim * 2);
        }
      }

      // Distance-based atmospheric fog
      var dist = Math.sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
      var fog = 1 - Math.min(1, dist / maxDist) * 0.35;
      op *= fog;

      // Depth-scroll fade: far tiles fade faster as camera advances
      op *= (1 - depthProgress * (0.15 + (1 - layerDepth) * 0.4));

      tile.el.style.transform = 'translate3d(' + (x - tile.halfW) + 'px,' + (y - tile.halfH) + 'px,0) scale(' + Math.max(0.01, scale).toFixed(3) + ')';
      tile.el.style.opacity = Math.max(0, Math.min(1, op)).toFixed(2);
      tile.el.style.zIndex = tile === focusedTile ? 20 : Math.round(tile.layer.speed * 10);
    }

    updatePanelVisibility();
  }

  var raf = null;
  function loop() {
    // Freeze all movement while a tile is focused
    if (focusedTile) {
      // Kill any residual velocity so it doesn't resume on un-focus
      velX = 0; velY = 0;
    } else if (pointerDown) {
      panX += (dragTargetX - panX) * 0.18;
      panY += (dragTargetY - panY) * 0.18;
    } else if (Math.abs(velX) > 0.02 || Math.abs(velY) > 0.02) {
      panX += velX;
      panY += velY;
      velX *= 0.94;
      velY *= 0.94;
    } else if (!REDUCED) {
      panX += driftVX;
      panY += driftVY;
    }

    // Smooth focus animation — slow lerp for cinematic feel
    var focusTarget = focusedTile ? 1 : 0;
    focusAnim += (focusTarget - focusAnim) * 0.04; // very slow for cinematic camera fly
    if (Math.abs(focusAnim - focusTarget) < 0.001) focusAnim = focusTarget;

    render();
    raf = requestAnimationFrame(loop);
  }

  function measureAndBuild() {
    build();
    render();
  }

  measureAndBuild();
  if (!REDUCED) {
    raf = requestAnimationFrame(loop);
  }
  setTimeout(function () { field.classList.add('is-ready'); }, 900);

  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      measureAndBuild();
      if (window.ScrollTrigger) window.ScrollTrigger.refresh();
    }, 180);
  });

  field.addEventListener('pointerdown', function (e) {
    pointerDown = true;
    velX = 0; velY = 0;
    startX = e.clientX; startY = e.clientY;
    dragStartPanX = panX; dragStartPanY = panY;
    dragTargetX = panX; dragTargetY = panY;
    lastX = e.clientX; lastY = e.clientY; lastMoveTime = performance.now();
    field.style.cursor = 'grabbing';
    field.classList.add('was-dragged');
  });
  window.addEventListener('pointerup', function () {
    if (!pointerDown) return;
    pointerDown = false;
    field.style.cursor = 'grab';
  });
  window.addEventListener('pointermove', function (e) {
    if (!pointerDown) return;
    dragTargetX = dragStartPanX + (e.clientX - startX);
    dragTargetY = dragStartPanY + (e.clientY - startY);

    var now = performance.now();
    var dt = now - lastMoveTime;
    if (dt > 0) {
      velX = Math.max(-30, Math.min(30, ((e.clientX - lastX)) * (16.67 / Math.max(dt, 1))));
      velY = Math.max(-30, Math.min(30, ((e.clientY - lastY)) * (16.67 / Math.max(dt, 1))));
    }
    lastX = e.clientX; lastY = e.clientY; lastMoveTime = now;

    if (REDUCED) { panX = dragTargetX; panY = dragTargetY; render(); }
  });

  /* ---------- Click: set vanishing point and fly the camera ---------- */
  field.addEventListener('click', function (e) {
    var tileEl = e.target.closest ? e.target.closest('.drift-tile') : null;
    var match = tileEl ? tiles.filter(function (t) { return t.el === tileEl; })[0] : null;
    var wasFocused = match && focusedTile === match;
    tiles.forEach(function (t) { t.el.classList.remove('is-focused'); });

    if (match && !wasFocused) {
      // Set the vanishing point to where this tile currently is on screen
      var rect = tileEl.getBoundingClientRect();
      var fieldRect = field.getBoundingClientRect();
      vpX = rect.left + rect.width / 2 - fieldRect.left;
      vpY = rect.top + rect.height / 2 - fieldRect.top;

      // Calculate offset to slide the tile to screen center
      var cx = containerW / 2;
      var cy = containerH / 2;
      focusCenterDX = cx - vpX;
      focusCenterDY = cy - vpY;

      // Kill any momentum so everything freezes
      velX = 0; velY = 0;

      focusedTile = match;
      tileEl.classList.add('is-focused');
    } else {
      focusedTile = null;
    }
    if (REDUCED) render();
  });

  // ---------- Desktop-only scroll-driven depth camera ----------
  if (!REDUCED && window.gsap && window.ScrollTrigger) {
    window.gsap.registerPlugin(window.ScrollTrigger);
    window.ScrollTrigger.matchMedia({
      '(min-width: 761px)': function () {
        var st = window.ScrollTrigger.create({
          trigger: section,
          start: 'top 95%',
          end: 'bottom 5%',
          scrub: 1.2,
          onUpdate: function (self) {
            depthProgress = self.progress;
          },
          onLeaveBack: function () {
            depthProgress = 0;
          },
          onLeave: function () {
            depthProgress = 1;
          }
        });

        return function () {
          depthProgress = 0;
          st.kill();
        };
      }
    });
  }
})();
