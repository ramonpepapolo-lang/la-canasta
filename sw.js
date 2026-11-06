// La Canasta app: works offline with the last prices it saw.
// Pages and data: network first (always today's prices when there is signal), the saved copy when there is none.
// Logos, icons and scripts: saved copy first (they rarely change).
const CACHE = "lc-app-v3";
const PRECACHE = ["/canastas/", "/canastas/datos.json", "/canastas/catalogo.json", "/app-datos/datos.json", "/counter.js?v=4", "/manifest.webmanifest",
  "/app-icons/icon-192.png", "/la-canasta-logo/la-canasta-logo-horizontal.svg", "/la-canasta-logo/la-canasta-icon.svg"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== CACHE).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;
  const isStatic = /\.(svg|png|jpg|woff2?|js)$/.test(u.pathname) && !u.pathname.endsWith("sw.js");
  if (isStatic) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => { if (r.ok) caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })));
  } else {
    e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true }).then(hit => hit || caches.match("/canastas/"))));
  }
});
