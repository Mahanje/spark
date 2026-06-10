const CACHE_VERSION = 'v5'; // ورژن را بالا بردیم تا کش قبلی پاک شود
const CACHE_NAME = `spark-cache-${CACHE_VERSION}`;

const STATIC_ASSETS = [
  '/', // صفحه اصلی حتما باید باشد
  '/static/css/base.css',
  '/static/css/navbar.css',
  '/static/css/videos.css',
  '/static/css/upload.css',
  '/manifest.json',
  '/static/images/icon-192.png', // دقیقا همان که در مانیفست است
  '/static/images/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching essential assets...');
        // از addAll استفاده می‌کنیم اما با احتیاط
        return cache.addAll(STATIC_ASSETS);
      })
      .catch(err => console.log('SW Install Error (Check your asset paths):', err))
  );
});