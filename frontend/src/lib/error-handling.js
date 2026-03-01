/**
 * Error Handling Utilities
 * Shows error toast on API failure, retries failed requests, fallback to cached data
 * 
 * Requirements: 2.2
 */

/**
 * Retry failed request with exponential backoff
 */
export const retryRequest = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (i < maxRetries - 1) {
        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  }

  throw lastError;
};

/**
 * Handle API error
 * Returns error message and logs to monitoring
 */
export const handleApiError = (error, context = '') => {
  const errorMessage = error?.message || 'An error occurred';

  // Log to monitoring service
  logErrorToMonitoring({
    message: errorMessage,
    context,
    timestamp: new Date().toISOString(),
    url: window.location.href,
  });

  return {
    message: errorMessage,
    isNetworkError: error?.message?.includes('network') || error?.message?.includes('fetch'),
    isTimeoutError: error?.message?.includes('timeout'),
  };
};

/**
 * Log error to monitoring service
 */
export const logErrorToMonitoring = (errorData) => {
  try {
    // In production, send to monitoring service
    if (process.env.NODE_ENV === 'production') {
      // Example: send to Sentry, LogRocket, etc.
      console.error('Monitoring:', errorData);
    } else {
      console.error('Dev Error:', errorData);
    }
  } catch (error) {
    console.error('Error logging to monitoring:', error);
  }
};

/**
 * Create error toast notification
 */
export const createErrorToast = (message, duration = 5000) => {
  const toast = document.createElement('div');
  toast.className = 'error-toast';
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.textContent = message;

  document.body.appendChild(toast);

  // Auto-remove after duration
  setTimeout(() => {
    toast.remove();
  }, duration);

  return toast;
};

/**
 * Create success toast notification
 */
export const createSuccessToast = (message, duration = 3000) => {
  const toast = document.createElement('div');
  toast.className = 'success-toast';
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.textContent = message;

  document.body.appendChild(toast);

  // Auto-remove after duration
  setTimeout(() => {
    toast.remove();
  }, duration);

  return toast;
};

/**
 * Validate API response
 */
export const validateApiResponse = (response, requiredFields = []) => {
  if (!response) {
    throw new Error('Empty response');
  }

  for (const field of requiredFields) {
    if (!(field in response)) {
      throw new Error(`Missing required field: ${field}`);
    }
  }

  return true;
};

/**
 * Handle network error
 */
export const handleNetworkError = (error) => {
  if (!navigator.onLine) {
    return {
      isOffline: true,
      message: 'You are offline. Changes will be synced when you reconnect.',
    };
  }

  return {
    isOffline: false,
    message: 'Network error. Please try again.',
  };
};

/**
 * Fallback to cached data
 */
export const fallbackToCachedData = (cachedData, errorMessage) => {
  if (cachedData) {
    return {
      data: cachedData,
      isCached: true,
      message: `Using cached data: ${errorMessage}`,
    };
  }

  return {
    data: null,
    isCached: false,
    message: errorMessage,
  };
};
