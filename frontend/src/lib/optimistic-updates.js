/**
 * Optimistic Updates Module
 * Implements optimistic UI updates with rollback on failure
 * Shows error toast if update fails
 * 
 * Requirements: 2.2
 */

/**
 * Perform optimistic update
 * Updates UI immediately, reverts on API failure
 */
export const performOptimisticUpdate = async (
  updateFn,
  revertFn,
  apiFn,
  onError
) => {
  try {
    // Update UI immediately
    updateFn();

    // Make API call
    const result = await apiFn();

    if (!result.ok) {
      throw new Error('API call failed');
    }

    return result;
  } catch (error) {
    // Revert UI on failure
    revertFn();

    // Show error toast
    if (onError) {
      onError(error.message);
    }

    throw error;
  }
};

/**
 * Create optimistic booking update
 */
export const createOptimisticBookingUpdate = (currentData, newBooking) => {
  const originalData = { ...currentData };

  const updateFn = () => {
    // Update would be handled by state management
    return {
      current_calls: (currentData.current_calls || 0) + 1,
      current_reservations: (currentData.current_reservations || 0) + 1,
      current_profit: (currentData.current_profit || 0) + (newBooking.profit || 0),
    };
  };

  const revertFn = () => {
    // Revert to original data
    return originalData;
  };

  return { updateFn, revertFn };
};

/**
 * Create optimistic income update
 */
export const createOptimisticIncomeUpdate = (currentData, newIncome) => {
  const originalData = { ...currentData };

  const updateFn = () => {
    return {
      current_profit: (currentData.current_profit || 0) + (newIncome.amount || 0),
      misc_income: (currentData.misc_income || 0) + (newIncome.amount || 0),
    };
  };

  const revertFn = () => {
    return originalData;
  };

  return { updateFn, revertFn };
};

/**
 * Create optimistic spin update
 */
export const createOptimisticSpinUpdate = (currentData, newSpin) => {
  const originalData = { ...currentData };

  const updateFn = () => {
    return {
      spins_total: (currentData.spins_total || 0) + 1,
    };
  };

  const revertFn = () => {
    return originalData;
  };

  return { updateFn, revertFn };
};
