/* ---------------------------------------------------------------
   VITALS — offline / rebrand interceptor

   The Elementis bundle is a live-CMS app: after hydration it refetches
   every page's content from vold-api.dev.fleava.com and re-renders from
   the response. That silently undid the rebrand (and made the "offline"
   clone phone home on every load).

   This shim runs BEFORE the Nuxt bundle and:
     1. serves those CMS calls from ./api-cache/ instead of the network
     2. neutralises the third-party beacons that shipped with the clone
        (Google Analytics, GTM, reCAPTCHA) so a local copy doesn't send
        traffic to someone else's property

   Must stay a classic, non-deferred script in <head>, ahead of Nuxt's
   module scripts, or the first fetch escapes.
   --------------------------------------------------------------- */
(function () {
  'use strict';

  var API = 'https://vold-api.dev.fleava.com/';
  var MAP = null;               // { "/v1/<id>/homepage?x=y": "/api-cache/....json" }

  // synchronous load so the map is ready before Nuxt's first request
  try {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api-cache/_index.json', false);
    xhr.send(null);
    if (xhr.status === 200) MAP = JSON.parse(xhr.responseText);
  } catch (e) {
    console.warn('[vitals] api-cache index unavailable; falling back to network');
  }

  // The CMS distinguishes pages only by a query blob:
  //   /page?where={"customUrl.en":"wellness"}&status=publish
  // The runtime and the captured URL can differ in percent-encoding, so
  // compare decoded, then fall back to matching the slug itself.
  //
  // Never fall back to "some other /page" — that silently served The Story's
  // content on every route.
  function slugOf(s) {
    var m = /customUrl\.[a-z]{2}"?\s*:\s*"([^"]+)"/.exec(s) ||
            /\/post\/slug\/([^?&/]+)/.exec(s);
    return m ? m[1] : null;
  }

  function localFor(url) {
    if (!MAP || url.indexOf(API) !== 0) return null;
    var key = '/' + url.slice(API.length);
    if (MAP[key]) return MAP[key];

    var dec;
    try { dec = decodeURIComponent(key); } catch (e) { dec = key; }
    for (var k in MAP) {
      var kd;
      try { kd = decodeURIComponent(k); } catch (e) { kd = k; }
      if (kd === dec) return MAP[k];
    }

    var bare = key.split('?')[0];
    var want = slugOf(dec);
    if (want) {
      for (var k2 in MAP) {
        if (k2.split('?')[0] !== bare) continue;
        var kd2;
        try { kd2 = decodeURIComponent(k2); } catch (e) { kd2 = k2; }
        if (slugOf(kd2) === want) return MAP[k2];
      }
      return null;   // known slug, no cache entry: go to network rather than lie
    }

    // no slug in the query at all (e.g. /navigation) — a bare match is safe
    var only = null, count = 0;
    for (var k3 in MAP) if (k3.split('?')[0] === bare) { only = MAP[k3]; count++; }
    return count === 1 ? only : null;
  }

  // hosts that exist only to report on the original site
  var BLOCKED = /googletagmanager\.com|google-analytics\.com|analytics\.google\.com|recaptcha\.net|gstatic\.com\/recaptcha|doubleclick\.net/;

  /* ---------- fetch ---------- */
  var nativeFetch = window.fetch;
  window.fetch = function (input, init) {
    var url = typeof input === 'string' ? input : (input && input.url) || '';

    var local = localFor(url);
    if (local) {
      return nativeFetch(local, { credentials: 'same-origin' }).then(function (r) {
        // hand back a response that looks like it came from the API
        return r.text().then(function (t) {
          return new Response(t, {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        });
      });
    }

    // Pages have been pruned, so some CMS endpoints no longer have a cached
    // copy. Falling through to the network would quietly put the live API
    // back in the loop and undo the offline guarantee, so an uncached CMS
    // call returns empty rather than escaping.
    if (url.indexOf(API) === 0) {
      return Promise.resolve(new Response('{"results":[],"total":0}', {
        status: 200, headers: { 'Content-Type': 'application/json' },
      }));
    }

    if (BLOCKED.test(url)) {
      return Promise.resolve(new Response('{}', {
        status: 200, headers: { 'Content-Type': 'application/json' },
      }));
    }

    return nativeFetch.apply(this, arguments);
  };

  /* ---------- XMLHttpRequest ---------- */
  var open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    var local = typeof url === 'string' ? localFor(url) : null;
    if (local) arguments[1] = local;
    else if (typeof url === 'string' && BLOCKED.test(url)) arguments[1] = '/api-cache/_empty.json';
    return open.apply(this, arguments);
  };

  /* ---------- <script src> beacons ---------- */
  // GTM/reCAPTCHA inject themselves as script tags, which fetch can't see.
  var setAttr = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (name, value) {
    if (this.tagName === 'SCRIPT' && name === 'src' && BLOCKED.test(String(value))) {
      return setAttr.call(this, 'data-vitals-blocked', String(value));
    }
    return setAttr.apply(this, arguments);
  };
  var srcDesc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, 'src');
  Object.defineProperty(HTMLScriptElement.prototype, 'src', {
    get: function () { return srcDesc.get.call(this); },
    set: function (v) {
      if (BLOCKED.test(String(v))) { this.setAttribute('data-vitals-blocked', String(v)); return; }
      srcDesc.set.call(this, v);
    },
    configurable: true,
  });

  window.__vitalsIntercept = { mapped: MAP ? Object.keys(MAP).length : 0 };
})();
