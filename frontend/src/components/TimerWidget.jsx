import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Clock, AlertCircle } from 'lucide-react';
import './TimerWidget.css';

/**
 * Timer Widget - Syncs with Backend
 * Calls /api/entries/{date}/timer/start, stop, and status endpoints
 * Loads elapsed_minutes from server on mount
 */
function TimerWidget() {
  const [timerState, setTimerState] = useState('idle');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);
  const API_BASE = process.env.REACT_APP_API_URL || 'https://kpi-tracker-1.onrender.com/api';

  // Get today's date in YYYY-MM-DD format
  const getToday = () => {
    const now = new Date();
    return now.toISOString().split('T')[0];
  };

  // Load current timer state from backend on mount
  useEffect(() => {
    const loadTimerState = async () => {
      try {
        const response = await fetch(`${API_BASE}/entries/${getToday()}/timer`, {
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
          const data = await response.json();
          // If a timer is running on the backend
          if (data.work_timer_start) {
            setTimerState('running');
            // Convert elapsed_minutes (from server) to seconds and set state
            setElapsedSeconds(Math.floor(data.elapsed_minutes * 60));
            // Calculate local start time so we can continue counting
            startTimeRef.current = Date.now() - (data.elapsed_minutes * 60 * 1000);
          } else {
            // Load the accumulated total_time_minutes but don't start counting
            setElapsedSeconds(Math.floor(data.total_time_minutes * 60));
            setTimerState('idle');
          }
        }
        setError(null);
      } catch (err) {
        console.error('Error loading timer state:', err);
        setError('Failed to load timer state');
      } finally {
        setIsLoading(false);
      }
    };

    loadTimerState();
  }, []);

  // Update current time every second
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timeInterval);
  }, []);

  // Format elapsed time as HH:MM:SS
  const formatElapsedTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Format current time
  const formatCurrentTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    });
  };

  // Format current date
  const formatCurrentDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Start timer - call backend endpoint
  const handleStart = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/entries/${getToday()}/timer/start`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to start timer: ${response.status}`);
      }
      
      const data = await response.json();
      setTimerState('running');
      // Use server's elapsed_minutes as the source of truth
      setElapsedSeconds(Math.floor(data.elapsed_minutes * 60));
      startTimeRef.current = Date.now() - (data.elapsed_minutes * 60 * 1000);

      // Start local interval to increment
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        const now = Date.now();
        const elapsed = Math.floor((now - startTimeRef.current) / 1000);
        setElapsedSeconds(elapsed);
      }, 1000);
    } catch (err) {
      console.error('Error starting timer:', err);
      setError(err.message);
    }
  };

  // Pause timer (local only - don't call backend)
  const handlePause = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setTimerState('paused');
  };

  // Stop timer - call backend endpoint and reset
  const handleStop = async () => {
    try {
      setError(null);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      const response = await fetch(`${API_BASE}/entries/${getToday()}/timer/stop`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to stop timer: ${response.status}`);
      }

      const data = await response.json();
      // Set elapsed to the accumulated total from backend
      setElapsedSeconds(Math.floor(data.total_time_minutes * 60));
      setTimerState('idle');
      startTimeRef.current = null;
    } catch (err) {
      console.error('Error stopping timer:', err);
      setError(err.message);
    }
  };

  // Resume timer
  const handleResume = async () => {
    try {
      setError(null);
      setTimerState('running');
      startTimeRef.current = Date.now() - (elapsedSeconds * 1000);

      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        const now = Date.now();
        const elapsed = Math.floor((now - startTimeRef.current) / 1000);
        setElapsedSeconds(elapsed);
      }, 1000);
    } catch (err) {
      console.error('Error resuming timer:', err);
      setError(err.message);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  if (isLoading) {
    return (
      <div className="timer-widget">
        <div className="timer-header">
          <Clock className="timer-icon" size={20} />
          <h3 className="timer-title">Time</h3>
        </div>
        <div className="timer-loading">Loading timer...</div>
      </div>
    );
  }

  return (
    <div className="timer-widget">
      <div className="timer-header">
        <Clock className="timer-icon" size={20} />
        <h3 className="timer-title">Time</h3>
      </div>

      {/* Error Display */}
      {error && (
        <div className="timer-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Current Time Display */}
      <div className="timer-current-time">
        <div className="current-time-value">{formatCurrentTime(currentTime)}</div>
        <div className="current-date-value">{formatCurrentDate(currentTime)}</div>
      </div>

      {/* Elapsed Time Display */}
      <div className="timer-elapsed">
        <div className="elapsed-value">{formatElapsedTime(elapsedSeconds)}</div>
        <div className="elapsed-label">Elapsed Time</div>
      </div>

      {/* Timer Controls */}
      <div className="timer-controls">
        {timerState === 'idle' && (
          <button 
            className="timer-btn timer-btn-start" 
            onClick={handleStart}
            disabled={!!error}
            aria-label="Start Timer"
          >
            <Play size={20} />
            <span>Start</span>
          </button>
        )}

        {timerState === 'running' && (
          <>
            <button 
              className="timer-btn timer-btn-pause" 
              onClick={handlePause}
              aria-label="Pause Timer"
            >
              <Pause size={20} />
              <span>Pause</span>
            </button>
            <button 
              className="timer-btn timer-btn-stop" 
              onClick={handleStop}
              aria-label="Stop Timer"
            >
              <Square size={20} />
              <span>Stop</span>
            </button>
          </>
        )}

        {timerState === 'paused' && (
          <>
            <button 
              className="timer-btn timer-btn-start" 
              onClick={handleResume}
              aria-label="Resume Timer"
            >
              <Play size={20} />
              <span>Resume</span>
            </button>
            <button 
              className="timer-btn timer-btn-stop" 
              onClick={handleStop}
              aria-label="Stop Timer"
            >
              <Square size={20} />
              <span>Stop</span>
            </button>
          </>
        )}
      </div>

      {/* Timer Status Indicator */}
      <div className={`timer-status status-${timerState}`}>
        <span className="status-dot"></span>
        <span className="status-text">
          {timerState === 'idle' && 'Ready'}
          {timerState === 'running' && 'Running'}
          {timerState === 'paused' && 'Paused'}
        </span>
      </div>
    </div>
  );
}

export default TimerWidget;

