import { useEffect, useRef, useCallback } from 'react';

/**
 * Smart polling hook for real-time updates
 * 
 * Only polls for Group plan users
 * Polls every 20 seconds
 * Stops polling when tab is hidden (saves resources)
 * Resumes when tab becomes visible
 */
export function useRealtimePolling(fetchFunction, options = {}) {
  const {
    enabled = true,
    interval = 20000, // 20 seconds
    plan = 'pro'
  } = options;

  const intervalRef = useRef(null);
  const isPollingRef = useRef(false);

  const startPolling = useCallback(() => {
    if (!enabled || plan !== 'group' || isPollingRef.current) {
      return;
    }

    isPollingRef.current = true;

    // Initial fetch
    fetchFunction();

    // Set up interval
    intervalRef.current = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchFunction();
      }
    }, interval);
  }, [enabled, plan, interval, fetchFunction]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    isPollingRef.current = false;
  }, []);

  useEffect(() => {
    // Only poll for Group plan
    if (plan === 'group' && enabled) {
      startPolling();
    }

    // Handle visibility change
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && plan === 'group' && enabled) {
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
  }, [plan, enabled, startPolling, stopPolling]);

  return { startPolling, stopPolling };
}
