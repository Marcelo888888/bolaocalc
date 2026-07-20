const CACHE_NAME = 'bolaocalc-v36';
const urlsToCache = [
  '.',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './qrcode.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Network-first: tenta o PC primeiro, cai pro cache so se estiver offline.
  // Assim o celular sempre pega a versao mais nova servida pelo PC (mesma rede).
  event.respondWith(
    fetch(req)
      .then((resp) => {
        // Atualiza o cache so com GET same-origin com status 200
        try {
          if (req.method === 'GET' && resp && resp.status === 200 &&
              new URL(req.url).origin === self.location.origin) {
            const copy = resp.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, copy)).catch(() => {});
          }
        } catch (e) { /* ignora */ }
        return resp;
      })
      .catch(() => caches.match(req))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});