const CACHE_NAME = 'steam-tables-cache-v3'; // Versión 3
const urlsToCache = [
  '/',
  '/static/styles.css',
  '/static/manifest.json', // Añadido el manifest a la caché
  '/static/icon-192.png',
  '/static/icon-512.png'
];

self.addEventListener('install', function(event) {
  // Forzar al nuevo service worker a activarse inmediatamente
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      console.log('Opened cache');
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('activate', function(event) {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    // Tomar el control de las páginas abiertas inmediatamente
    .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', function(event) {
    // Estrategia: Network falling back to cache
    event.respondWith(
        fetch(event.request).catch(function() {
            return caches.match(event.request);
        })
    );
});
