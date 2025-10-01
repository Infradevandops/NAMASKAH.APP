const CACHE_NAME = 'namaskah-app-v2';
const STATIC_CACHE = 'namaskah-app-static-v2';
const DYNAMIC_CACHE = 'namaskah-app-dynamic-v2';
const API_CACHE = 'namaskah-app-api-v2';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/css/enhanced-chat.css',
  '/static/js/enhanced-chat.js',
  '/static/js/security.js',
  '/static/css/enhanced-chat-search.css',
  '/static/js/enhanced-chat-search.js',
  '/static/manifest.json',
  '/performance'
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/info',
  '/api/auth/me'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Error caching static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE && cacheName !== API_CACHE) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated successfully');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  }
  // Handle static assets and pages
  else {
    event.respondWith(handleStaticRequest(request));
  }
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);

    // If successful, cache the response
    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache for API:', request.url);

    // Try cache as fallback
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline message for API requests
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'This feature requires an internet connection'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
  // Try cache first
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    // Fetch from network
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Failed to fetch:', request.url);

    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match('/');
      if (offlineResponse) {
        return offlineResponse;
      }
    }

    // Return a generic offline response
    return new Response(
      'Offline - Please check your internet connection',
      {
        status: 503,
        headers: { 'Content-Type': 'text/plain' }
      }
    );
  }
}

// Handle background sync for messages
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync-messages') {
    console.log('Service Worker: Background sync triggered');
    event.waitUntil(syncMessages());
  }
});

// Background sync for messages
async function syncMessages() {
  try {
    // This would sync pending messages when connection is restored
    console.log('Service Worker: Syncing pending messages...');

    // Get pending messages from IndexedDB (if implemented)
    // Send them to the server
    // Update local state

    console.log('Service Worker: Messages synced successfully');
  } catch (error) {
    console.error('Service Worker: Background sync failed:', error);
  }
}

// Handle push notifications
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'New message received',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/badge-72x72.png',
      data: data.data || {},
      actions: [
        {
          action: 'view',
          title: 'View',
          icon: '/static/icons/view-icon.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/static/icons/close-icon.png'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification(data.title || 'CumApp', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'view') {
    // Open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message handling for communication with the main thread
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});