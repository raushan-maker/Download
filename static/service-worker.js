
self.addEventListener('install', function(e) {
  console.log('Service Worker: Installed');
  e.waitUntil(
    caches.open('video-downloader-cache').then(function(cache) {
      return cache.addAll([
        '/',
        '/static/logo.png',
        '/manifest.json'
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
