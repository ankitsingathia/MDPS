/* ---------------------------------------------------------------
   VITALS brand layer

   Runs on top of the compiled Elementis bundle. Two jobs:
     1. show the VITALS preloader instead of the ELEMENTIS one
     2. swap every 216px ELEMENTIS wordmark for a VITALS one

   Nuxt re-renders on hydration and on client-side route changes,
   so the wordmark swap runs again whenever the DOM changes.
   --------------------------------------------------------------- */
(function () {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';

  /* ---------- 1. preloader ---------- */

  // letters sit on baseline y=110; the I slot (x=170) stays empty
  // until the ECG spike settles into it.
  var MARK =
    '<svg class="mark" id="v-mark" viewBox="0 0 580 176" aria-label="VITALS">' +
      '<g fill="#d1ccbf" font-family="Basis Grotesque,sans-serif" font-size="64"' +
      ' font-weight="300" text-anchor="middle">' +
        '<text class="ltr" x="90"  y="110">V</text>' +
        '<text class="ltr" x="250" y="110">T</text>' +
        '<text class="ltr" x="330" y="110">A</text>' +
        '<text class="ltr" x="410" y="110">L</text>' +
        '<text class="ltr" x="490" y="110">S</text>' +
        '<text id="v-eye" x="170" y="110">I</text>' +
      '</g>' +
      '<path id="v-trace" d="M 8 136 L 108 136 q 8 0 12 -7 q 4 7 12 7 L 156 136' +
      ' L 164 136 L 170 66 L 176 154 L 182 136 L 300 136 q 10 0 16 -9 q 6 9 16 9' +
      ' L 572 136"/>' +
    '</svg>';

  function preload() {
    if (document.getElementById('vitals-pre')) return;

    var pre = document.createElement('div');
    pre.id = 'vitals-pre';
    pre.innerHTML = MARK;
    document.body.appendChild(pre);

    var trace = pre.querySelector('#v-trace');
    var eye   = pre.querySelector('#v-eye');
    var mark  = pre.querySelector('#v-mark');
    var ltrs  = [].slice.call(pre.querySelectorAll('.ltr'));

    // prime the trace for a draw-on
    var len = trace.getTotalLength();
    trace.style.strokeDasharray  = len;
    trace.style.strokeDashoffset = len;

    var at = function (ms, fn) { setTimeout(fn, ms); };

    // 1. letters rise in, 100ms apart (V T A L S — the I is absent)
    ltrs.forEach(function (l, i) {
      at(200 + i * 100, function () { l.classList.add('in'); });
    });

    // 2. ECG draws left -> right
    at(900, function () {
      trace.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(.22,1,.36,1)';
      trace.style.strokeDashoffset = 0;
    });

    // 3. the spike settles into the letter I, the trace dissolves
    at(2150, function () { eye.classList.add('in'); });
    at(2320, function () { trace.classList.add('fade'); });

    // 4. hold, then lift
    at(3250, function () { mark.classList.add('out'); });
    at(3600, function () { pre.classList.add('lift'); });
    at(4800, function () { pre.classList.add('done'); });
  }

  /* ---------- 2. header wordmark ---------- */

  function vitalsLogo() {
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'v-logo');
    svg.setAttribute('viewBox', '0 0 132 17');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('aria-label', 'VITALS');
    svg.innerHTML =
      '<text x="0" y="14" font-size="15" letter-spacing="3.6">VITALS</text>';
    return svg;
  }

  // The original wordmark is the only 216-wide svg on the page.
  //
  // We hide it and insert ours alongside rather than replacing it: Vue keeps
  // references to its own SSR nodes, and removing one out from under it throws
  // "Cannot read properties of null (reading 'nextSibling')" during hydration.
  // Hiding leaves Vue's DOM intact.
  function swapLogos(root) {
    var found = (root || document).querySelectorAll('svg[width="216"]:not([data-vitals-hidden])');
    for (var i = 0; i < found.length; i++) {
      var old = found[i];
      old.setAttribute('data-vitals-hidden', '1');
      old.style.display = 'none';
      var next = vitalsLogo();
      if (old.parentNode) old.parentNode.insertBefore(next, old);
    }
  }

  /* ---------- 3. "Try Demo" button ---------- */

  // Sits beside "Start Screening" as the lower-commitment entry point: it
  // will load a worked example with the form pre-filled, because most people
  // do not know their own serum creatinine off the top of their head.
  // The header CTA is a <div class="btn"> inside .hamburger-wrapper — not an
  // anchor — so it has to be matched structurally rather than by tag.
  function addDemoButton(root) {
    var scope = root || document;
    var wraps = scope.querySelectorAll('header .hamburger-wrapper');
    for (var i = 0; i < wraps.length; i++) {
      var wrap = wraps[i];
      if (wrap.querySelector('.v-demo')) continue;
      var cta = wrap.querySelector('.btn');
      if (!cta) continue;

      var demo = document.createElement('a');
      demo.className = 'v-demo';
      demo.href = '/destinations';
      demo.textContent = 'Try Demo';
      wrap.insertBefore(demo, cta);
    }
  }

  /* ---------- boot ---------- */

  function boot() {
    preload();

    // Wait for hydration to settle before touching Vue-owned DOM. Our curtain
    // is up for ~3.6s, so a swap at ~1.2s is never visible to the user.
    function start() {
      setTimeout(function () {
        swapLogos(document);
        addDemoButton(document);
        // Client-side route changes re-render the header, so keep re-applying.
        new MutationObserver(function () {
          swapLogos(document);
          addDemoButton(document);
        }).observe(document.body, { childList: true, subtree: true });
      }, 1200);
    }

    if (document.readyState === 'complete') start();
    else window.addEventListener('load', start);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
