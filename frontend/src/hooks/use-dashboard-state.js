import { useState, useCallback, useEffect } from 'react';

/**
 * Dashboard State Management Hook
 * Manages current day's entry data, daily goals, timer state, and UI state
 * Implements caching with 5 minute TTL
 * 
 * Requirements: 2.1, 2.2
 */

const CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

export function useDashboardState(userId) {
  const [entryData, setEntryData] = useState(null);
  const [dailyGoals, setDailyGoals] = useState(null);
  const [timerState, setTimerState] = useState({
    running: false,
    paused: false,
    elapsedSeconds: 0,
  });
  const [uiState, setUiState] = useState({
    expandedSections: {
      goals: true,
      stats: true,
      actions: true,
    },
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cacheTime, setCacheTime] = useState(null);

  // Fetch current day's entry
  const fetchEntryData = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const today = new Date().toISOString().split('T')[0];

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/entries/${today}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch entry data');
      }

      const data = await response.json();
      setEntryData(data);
      setCacheTime(Date.now());
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Entry data fetch error:', err);
    }
  }, []);

  // Fetch daily goals
  const fetchDailyGoals = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/goals/current`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch daily goals');
      }

      const data = await response.json();
      setDailyGoals(data.daily);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Daily goals fetch error:', err);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    const fetchAllData = async () => {
      setLoading(true);
      await Promise.all([fetchEntryData(), fetchDailyGoals()]);
      setLoading(false);
    };

    if (userId) {
      fetchAllData();
    }
  }, [userId, fetchEntryData, fetchDailyGoals]);

  // Check cache validity
  const isCacheValid = useCallback(() => {
    if (!cacheTime) return false;
    return Date.now() - cacheTime < CACHE_TTL;
  }, [cacheTime]);

  // Update entry data with optimistic update
  const updateEntryData = useCallback((updates) => {
    setEntryData(prev => ({
      ...prev,
      ...updates,
    }));
  }, []);

  // Toggle section expansion
  const toggleSection = useCallback((section) => {
    setUiState(prev => ({
      ...prev,
      expandedSections: {
        ...prev.expandedSections,
        [section]: !prev.expandedSections[section],
      },
    }));
  }, []);

  // Update timer state
  const updateTimerState = useCallback((updates) => {
    setTimerState(prev => ({
      ...prev,
      ...updates,
    }));
  }, []);

  // Refresh data if cache expired
  const refreshIfNeeded = useCallback(async () => {
    if (!isCacheValid()) {
      await Promise.all([fetchEntryData(), fetchDailyGoals()]);
    }
  }, [isCacheValid, fetchEntryData, fetchDailyGoals]);

  return {
    entryData,
    dailyGoals,
    timerState,
    uiState,
    loading,
    error,
    updateEntryData,
    toggleSection,
    updateTimerState,
    fetchEntryData,
    fetchDailyGoals,
    refreshIfNeeded,
    isCacheValid,
  };
}
