// VAPID public key for Web Push — replace with real key from backend
const VAPID_PUBLIC_KEY = 'BEl62iUYgUivxIkv69yViE1eUVJdrWxt8LhR8tZJXR8N8I9y8I6o9_2l9s5f_0oBCVG3p5nVl9LJ_-8D5MlhBrE';

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function requestPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.warn('[Push] Notifications not supported');
    return 'denied';
  }
  return await Notification.requestPermission();
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.warn('[Push] Service Workers not supported');
    return null;
  }
  try {
    const registration = await navigator.serviceWorker.register('/sw.js');
    console.log('[Push] Service Worker registered:', registration.scope);
    return registration;
  } catch (error) {
    console.error('[Push] Service Worker registration failed:', error);
    return null;
  }
}

export async function subscribe(
  registration: ServiceWorkerRegistration
): Promise<PushSubscription | null> {
  try {
    const existingSubscription = await registration.pushManager.getSubscription();
    if (existingSubscription) {
      return existingSubscription;
    }

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    });
    console.log('[Push] Subscribed:', subscription);
    return subscription;
  } catch (error) {
    console.error('[Push] Subscription failed:', error);
    return null;
  }
}

export function showNotification(
  title: string,
  body: string,
  options?: NotificationOptions
): void {
  if (Notification.permission !== 'granted') {
    console.warn('[Push] Notification permission not granted');
    return;
  }

  try {
    new Notification(title, {
      body,
      icon: '/icons/icon-192x192.png',
      badge: '/icons/badge-72x72.png',
      ...options,
    });
  } catch (error) {
    console.error('[Push] Failed to show notification:', error);
  }
}

export const pushService = {
  requestPermission,
  registerServiceWorker,
  subscribe,
  showNotification,
};
