/**
 * Offline Support Module
 * Displays cached data when offline
 * Queues updates for when online
 * Syncs queued updates when connection restored
 * 
 * Requirements: 3.5
 */

const QUEUE_STORAGE_KEY = 'dashboard_update_queue';
const CACHE_STORAGE_KEY = 'dashboard_cache';

/**
 * Get cached dashboard data
 */
export const getCachedData = () => {
  try {
    const cached = localStorage.getItem(CACHE_STORAGE_KEY);
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (error) {
    console.error('Error reading cache:', error);
  }
  return null;
};

/**
 * Save dashboard data to cache
 */
export const saveCacheData = (data) => {
  try {
    localStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error('Error saving cache:', error);
  }
};

/**
 * Queue update for later sync
 */
export const queueUpdate = (update) => {
  try {
    const queue = getUpdateQueue();
    queue.push({
      ...update,
      timestamp: Date.now(),
    });
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
  } catch (error) {
    console.error('Error queuing update:', error);
  }
};

/**
 * Get all queued updates
 */
export const getUpdateQueue = () => {
  try {
    const queue = localStorage.getItem(QUEUE_STORAGE_KEY);
    if (queue) {
      return JSON.parse(queue);
    }
  } catch (error) {
    console.error('Error reading queue:', error);
  }
  return [];
};

/**
 * Clear update queue
 */
export const clearUpdateQueue = () => {
  try {
    localStorage.removeItem(QUEUE_STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing queue:', error);
  }
};

/**
 * Sync queued updates when online
 */
export const syncQueuedUpdates = async (syncFn) => {
  const queue = getUpdateQueue();

  if (queue.length === 0) {
    return { success: true, synced: 0 };
  }

  let synced = 0;

  for (const update of queue) {
    try {
      await syncFn(update);
      synced++;
    } catch (error) {
      console.error('Error syncing update:', error);
      // Continue with next update
    }
  }

  if (synced === queue.length) {
    clearUpdateQueue();
  }

  return { success: synced > 0, synced };
};

/**
 * Check if online
 */
export const isOnline = () => {
  return navigator.onLine;
};

/**
 * Listen for online/offline events
 */
export const listenForConnectivityChanges = (onOnline, onOffline) => {
  const handleOnline = () => {
    if (onOnline) onOnline();
  };

  const handleOffline = () => {
    if (onOffline) onOffline();
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
};
