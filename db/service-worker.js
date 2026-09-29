// PS4 Games Database - Service Worker
// Provides offline functionality by caching all necessary files

const CACHE_NAME = 'ps4-games-db-v1';
const CACHE_VERSION = '1.0.0';

// Files to cache for offline functionality
const CACHE_FILES = [
    './',
    './ps4-pwa-optimized.html',
    './ps4_games_with_downloads.json',
    './manifest.json',
    './gamepad-controller.js'
];

// Install event - cache all necessary files
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching files');
                return cache.addAll(CACHE_FILES);
            })
            .then(() => {
                console.log('[Service Worker] All files cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[Service Worker] Cache failed:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[Service Worker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[Service Worker] Activated successfully');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                // Return cached version if available
                if (cachedResponse) {
                    console.log('[Service Worker] Serving from cache:', event.request.url);
                    return cachedResponse;
                }
                
                // Otherwise fetch from network
                console.log('[Service Worker] Fetching from network:', event.request.url);
                return fetch(event.request)
                    .then((response) => {
                        // Don't cache if not a valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clone the response
                        const responseToCache = response.clone();
                        
                        // Cache the fetched response for future use
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch((error) => {
                        console.error('[Service Worker] Fetch failed:', error);
                        
                        // Return offline page if available
                        return caches.match('./ps4-pwa-optimized.html');
                    });
            })
    );
});

// Message event - handle messages from the app
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        return caches.delete(cacheName);
                    })
                );
            })
        );
    }
});

// Background sync for future updates
self.addEventListener('sync', (event) => {
    if (event.tag === 'update-database') {
        event.waitUntil(updateDatabase());
    }
});

// Function to update database in background
async function updateDatabase() {
    try {
        const response = await fetch('./ps4_games_with_downloads.json');
        const cache = await caches.open(CACHE_NAME);
        await cache.put('./ps4_games_with_downloads.json', response);
        console.log('[Service Worker] Database updated successfully');
    } catch (error) {
        console.error('[Service Worker] Database update failed:', error);
    }
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'update-database-periodic') {
        event.waitUntil(updateDatabase());
    }
});

console.log('[Service Worker] Loaded successfully');
