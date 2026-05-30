// Service Worker for Vocal Calendar push notifications
const CACHE_NAME = 'vocal-calendar-v1';

// Install event — skip waiting to activate immediately
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

// Activate event — claim existing clients
self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Push event — show notification when a push message arrives
self.addEventListener('push', (event) => {
  let data = { title: 'Vocal Calendar', body: '您有一个新的提醒' };

  if (event.data) {
    try {
      data = event.data.json();
    } catch {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    vibrate: [200, 100, 200],
    tag: data.tag || 'reminder',
    data: data.url || '/',
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

// Notification click — focus existing window or open a new one
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const targetUrl = event.notification.data || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // If a window is already open, focus it
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      // Otherwise open a new window
      return self.clients.openWindow(targetUrl);
    }),
  );
});
