/**
 * Performance Optimization Utilities
 * Lazy loading, debouncing, memoization, virtual scrolling, caching
 * 
 * Requirements: 2.2
 */

/**
 * Debounce function
 * Delays function execution until after specified delay
 */
export const debounce = (fn, delay) => {
  let timeoutId;

  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      fn(...args);
    }, delay);
  };
};

/**
 * Throttle function
 * Limits function execution to once per specified interval
 */
export const throttle = (fn, interval) => {
  let lastCall = 0;

  return (...args) => {
    const now = Date.now();
    if (now - lastCall >= interval) {
      lastCall = now;
      fn(...args);
    }
  };
};

/**
 * Memoize function results
 * Caches function results based on arguments
 */
export const memoize = (fn) => {
  const cache = new Map();

  return (...args) => {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = fn(...args);
    cache.set(key, result);

    return result;
  };
};

/**
 * Lazy load component
 * Loads component only when visible in viewport
 */
export const lazyLoadComponent = (element, callback) => {
  if (!('IntersectionObserver' in window)) {
    // Fallback for browsers without IntersectionObserver
    callback();
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          callback();
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  observer.observe(element);

  return observer;
};

/**
 * Cache API response
 * Stores response with TTL
 */
export const cacheResponse = (key, data, ttl = 5 * 60 * 1000) => {
  const cacheData = {
    data,
    timestamp: Date.now(),
    ttl,
  };

  try {
    sessionStorage.setItem(key, JSON.stringify(cacheData));
  } catch (error) {
    console.error('Error caching response:', error);
  }
};

/**
 * Get cached response
 * Returns cached data if not expired
 */
export const getCachedResponse = (key) => {
  try {
    const cached = sessionStorage.getItem(key);
    if (!cached) return null;

    const { data, timestamp, ttl } = JSON.parse(cached);

    if (Date.now() - timestamp > ttl) {
      sessionStorage.removeItem(key);
      return null;
    }

    return data;
  } catch (error) {
    console.error('Error retrieving cached response:', error);
    return null;
  }
};

/**
 * Clear cache
 */
export const clearCache = (key) => {
  try {
    if (key) {
      sessionStorage.removeItem(key);
    } else {
      sessionStorage.clear();
    }
  } catch (error) {
    console.error('Error clearing cache:', error);
  }
};

/**
 * Request idle callback polyfill
 */
export const requestIdleCallback = (callback, options = {}) => {
  if ('requestIdleCallback' in window) {
    return window.requestIdleCallback(callback, options);
  }

  const start = Date.now();
  return setTimeout(() => {
    callback({
      didTimeout: false,
      timeRemaining: () => Math.max(0, 50 - (Date.now() - start)),
    });
  }, 1);
};

/**
 * Cancel idle callback
 */
export const cancelIdleCallback = (id) => {
  if ('cancelIdleCallback' in window) {
    window.cancelIdleCallback(id);
  } else {
    clearTimeout(id);
  }
};
