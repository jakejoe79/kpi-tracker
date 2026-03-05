import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Clock, AlertCircle } from 'lucide-react';
import './TimerWidget.css';

/**
 * Timer Widget - Modern Clock Design
 * Digital clock interface with punch clock style
 * Syncs with backend for persistent timing
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
          if (data.work_timer_start) {
            setTimerState('running');
            setElapsedSeconds(Math.floor(data.elapsed_minutes * 60));
            startTimeRef.current = Date.now() - (data.elapsed_minutes * 60 * 1000);
          } else {
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
        <h3 className="timer-title">Work Clock</h3>
      </div>

      {/* Error Display */}
      {error && (
        <div className="timer-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Clock Display */}
      <div className="clock-display">
        <div className="clock-face">
          <div className="elapsed-time">{formatElapsedTime(elapsedSeconds)}</div>
          <div className="time-label">WORK TIME</div>
        </div>
        
        {/* Status Badge */}
        <div className={`status-badge status-${timerState}`}>
          {timerState === 'idle' && 'OFF DUTY'}
          {timerState === 'running' && 'ON DUTY'}
          {timerState === 'paused' && 'BREAK'}
        </div>
      </div>

      {/* Control Panel */}
      <div className="control-panel">
        {timerState === 'idle' && (
          <button 
            className="clock-btn clock-btn-punch-in" 
            onClick={handleStart}
            disabled={!!error}
          >
            <Play size={18} />
            PUNCH IN
          </button>
        )}

        {timerState === 'running' && (
          <div className="control-row">
            <button 
              className="clock-btn clock-btn-break" 
              onClick={handlePause}
            >
              <Pause size={18} />
              BREAK
            </button>
            <button 
              className="clock-btn clock-btn-punch-out" 
              onClick={handleStop}
            >
              <Square size={18} />
              PUNCH OUT
            </button>
          </div>
        )}

        {timerState === 'paused' && (
          <div className="control-row">
            <button 
              className="clock-btn clock-btn-resume" 
              onClick={handleResume}
            >
              <Play size={18} />
              RESUME
            </button>
            <button 
              className="clock-btn clock-btn-punch-out" 
              onClick={handleStop}
            >
              <Square size={18} />
              PUNCH OUT
            </button>
          </div>
        )}
      </div>

      {/* Current Time */}
      <div className="current-time-display">
        {formatCurrentTime(currentTime)}
      </div>
    </div>
  );
}

export default TimerWidget;

