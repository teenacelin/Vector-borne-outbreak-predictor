const CACHE_NAME = 'vectorpredict-cache-v2';
const DYNAMIC_CACHE = 'vectorpredict-api-v2';

const CORE_ASSETS = [
    './index.html',
    './js/dashboard.js',
    './manifest.json',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// Install Event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching Core Assets');
            return cache.addAll(CORE_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate Event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME && key !== DYNAMIC_CACHE) {
                        console.log('[Service Worker] Removing Old Cache', key);
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch Event
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // If it's an API call, try Network first, then fallback to Cache
    if (url.pathname.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then((networkResponse) => {
                    // Cache the successful API response for offline use
                    return caches.open(DYNAMIC_CACHE).then((cache) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                })
                .catch(() => {
                    // Offline? Return the cached API response
                    console.warn('[Service Worker] Offline! Serving API from cache.');
                    return caches.match(event.request);
                })
        );
        return;
    }

    // For static assets, try Cache first, then Network
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || fetch(event.request);
        })
    );
});
