self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open('steam-tables-cache').then(function(cache) {
      return cache.addAll([
        '/',
        '/static/styles.css',
        '/static/icon-192.png',
        '/static/icon-512.png'
      ]);
    })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});
