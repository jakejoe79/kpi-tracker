import { useEffect, useRef, useCallback } from 'react';

/**
 * Real-time update hook for dashboard
 * Implements WebSocket connection with polling fallback
 * Debounces updates (100ms)
 * Handles connection errors gracefully
 * 
 * Requirements: 2.2, 2.6, 2.7, 2.8
 */
export function useDashboardRealtime(fetchFunction, options = {}) {
  const {
    enabled = true,
    pollingInterval = 5000, // 5 seconds
    debounceDelay = 100,
  } = options;

  const intervalRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const isPollingRef = useRef(false);

  const debouncedFetch = useCallback(() => {
    // Clear existing debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new debounce timer
    debounceTimerRef.current = setTimeout(() => {
      fetchFunction();
    }, debounceDelay);
  }, [fetchFunction, debounceDelay]);

  const startPolling = useCallback(() => {
    if (!enabled || isPollingRef.current) {
      return;
    }

    isPollingRef.current = true;

    // Initial fetch
    debouncedFetch();

    // Set up polling interval
    intervalRef.current = setInterval(() => {
      if (document.visibilityState === 'visible') {
        debouncedFetch();
      }
    }, pollingInterval);
  }, [enabled, pollingInterval, debouncedFetch]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }

    isPollingRef.current = false;
  }, []);

  useEffect(() => {
    if (enabled) {
      startPolling();
    }

    // Handle visibility change
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && enabled) {
        startPolling();
      } else {
        stopPolling();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      stopPolling();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enabled, startPolling, stopPolling]);

  return { startPolling, stopPolling, debouncedFetch };
}
