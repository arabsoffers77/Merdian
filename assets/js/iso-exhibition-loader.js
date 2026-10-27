/* Choose a compatible build while preserving the same React/Three.js design. */
(function () {
  'use strict';
  var source = document.currentScript;
  if (!source || !document.getElementById('certification-app')) return;
  var local = location.protocol === 'file:';
  var script = document.createElement('script');
  var url = new URL('./iso-exhibition/' + (local ? 'local.js' : 'index.js'), source.src);
  url.search = new URL(source.src).search;
  if (!local) script.type = 'module';
  script.src = url.href;
  document.head.appendChild(script);
})();
