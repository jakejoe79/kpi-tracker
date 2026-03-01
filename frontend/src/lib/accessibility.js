/**
 * Accessibility Utilities
 * ARIA labels, keyboard navigation, high contrast, screen reader friendly
 * 
 * Requirements: 2.1, 2.5
 */

/**
 * Generate ARIA label for progress bar
 */
export const getProgressAriaLabel = (label, current, target, percentage) => {
  return `${label}: ${Math.round(percentage)}% complete, ${current} of ${target}`;
};

/**
 * Generate ARIA label for pace indicator
 */
export const getPaceAriaLabel = (pace) => {
  const labels = {
    'on-track': 'On track to reach daily goals',
    'moderate': 'Moderately on pace to reach daily goals',
    'behind': 'Behind pace to reach daily goals',
  };
  return labels[pace] || 'Pace indicator';
};

/**
 * Generate ARIA label for time remaining
 */
export const getTimeRemainingAriaLabel = (hours, minutes) => {
  return `${hours} hours and ${minutes} minutes remaining to reach daily target`;
};

/**
 * Generate ARIA label for stat item
 */
export const getStatAriaLabel = (label, value) => {
  return `${label}: ${value}`;
};

/**
 * Keyboard navigation handler
 */
export const handleKeyboardNavigation = (event, callbacks) => {
  const { onEnter, onSpace, onEscape, onArrowUp, onArrowDown } = callbacks;

  switch (event.key) {
    case 'Enter':
      if (onEnter) onEnter();
      break;
    case ' ':
      if (onSpace) {
        event.preventDefault();
        onSpace();
      }
      break;
    case 'Escape':
      if (onEscape) onEscape();
      break;
    case 'ArrowUp':
      if (onArrowUp) {
        event.preventDefault();
        onArrowUp();
      }
      break;
    case 'ArrowDown':
      if (onArrowDown) {
        event.preventDefault();
        onArrowDown();
      }
      break;
    default:
      break;
  }
};

/**
 * Focus management utilities
 */
export const focusElement = (element) => {
  if (element) {
    element.focus();
  }
};

export const focusFirstFocusableElement = (container) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (focusableElements.length > 0) {
    focusableElements[0].focus();
  }
};

/**
 * Announce to screen readers
 */
export const announceToScreenReader = (message, priority = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * High contrast mode detection
 */
export const isHighContrastMode = () => {
  if (window.matchMedia) {
    return window.matchMedia('(prefers-contrast: more)').matches;
  }
  return false;
};

/**
 * Reduced motion detection
 */
export const prefersReducedMotion = () => {
  if (window.matchMedia) {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
  return false;
};
