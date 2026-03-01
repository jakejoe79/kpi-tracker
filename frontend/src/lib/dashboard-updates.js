/**
 * Dashboard Update Handlers
 * Handles real-time updates for bookings, spins, income, and timer
 * 
 * Requirements: 2.2, 2.6, 2.7, 2.8
 */

/**
 * Handle booking update
 * Updates calls, bookings, profit, conversion rate
 * Recalculates time remaining
 */
export const handleBookingUpdate = (currentData, newBooking) => {
  if (!currentData) return currentData;

  const updatedData = { ...currentData };

  // Update calls (increment by 1)
  updatedData.current_calls = (updatedData.current_calls || 0) + 1;

  // Update bookings/reservations
  updatedData.current_reservations = (updatedData.current_reservations || 0) + 1;

  // Update profit
  updatedData.current_profit = (updatedData.current_profit || 0) + (newBooking.profit || 0);

  // Recalculate progress
  updatedData.progress_percent = calculateProgressPercent(
    updatedData.current_profit,
    updatedData.profit_target
  );

  return updatedData;
};

/**
 * Handle spin update
 * Updates spins total
 */
export const handleSpinUpdate = (currentData, newSpin) => {
  if (!currentData) return currentData;

  const updatedData = { ...currentData };
  updatedData.spins_total = (updatedData.spins_total || 0) + 1;

  return updatedData;
};

/**
 * Handle income update
 * Updates misc income total
 */
export const handleIncomeUpdate = (currentData, newIncome) => {
  if (!currentData) return currentData;

  const updatedData = { ...currentData };
  updatedData.misc_income = (updatedData.misc_income || 0) + (newIncome.amount || 0);

  // Update total profit if applicable
  updatedData.current_profit = (updatedData.current_profit || 0) + (newIncome.amount || 0);

  // Recalculate progress
  updatedData.progress_percent = calculateProgressPercent(
    updatedData.current_profit,
    updatedData.profit_target
  );

  return updatedData;
};

/**
 * Handle timer update
 * Updates time worked every second
 * Recalculates time remaining
 */
export const handleTimerUpdate = (currentData, secondsElapsed) => {
  if (!currentData) return currentData;

  const updatedData = { ...currentData };

  // Update time worked (convert seconds to minutes)
  const minutesElapsed = Math.floor(secondsElapsed / 60);
  updatedData.total_time_minutes = (updatedData.total_time_minutes || 0) + minutesElapsed;

  // Recalculate time remaining
  updatedData.time_remaining_minutes = Math.max(
    0,
    (updatedData.time_needed_minutes || 0) - updatedData.total_time_minutes
  );

  return updatedData;
};

/**
 * Calculate progress percentage
 * progress_percent = (current / target) * 100
 */
export const calculateProgressPercent = (current, target) => {
  if (!target || target === 0) return 0;
  return Math.min((current / target) * 100, 100);
};

/**
 * Determine pace indicator
 * ON TRACK: >= 75%
 * MODERATE: 50-74%
 * BEHIND: < 50%
 */
export const getPaceIndicator = (progressPercent) => {
  if (progressPercent >= 75) return 'ON_TRACK';
  if (progressPercent >= 50) return 'MODERATE';
  return 'BEHIND';
};

/**
 * Get color coding for progress
 * green: >= 75%
 * yellow: 50-74%
 * red: < 50%
 */
export const getProgressColor = (progressPercent) => {
  if (progressPercent >= 75) return 'green';
  if (progressPercent >= 50) return 'yellow';
  return 'red';
};

/**
 * Validate data consistency
 * Ensures dashboard data matches expected format
 */
export const validateDashboardData = (data) => {
  if (!data) return false;

  const requiredFields = [
    'profit_target',
    'calls_needed',
    'reservations_needed',
    'current_profit',
    'current_calls',
    'current_reservations',
  ];

  return requiredFields.every(field => field in data);
};
