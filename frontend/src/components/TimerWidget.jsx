import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, Square, Clock } from 'lucide-react';
import './TimerWidget.css';

/**
 * Timer Widget Component
 * 
 * Features:
 * - Displays current time and date
 * - Start/stop/pause/resume timer functionality
 * - State validation prevents multiple concurrent timer starts
 * 
 * Bug Fix: Timer Multiple Starts Bug (Bug #1)
 * - Prevents creating multiple intervals when start is clicked rapidly
 * - Validates timerState before starting
 */
function TimerWidget() {
  // Timer state: 'idle', 'running', 'paused'
  const [timerState, setTimerState] = useState('idle');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);

  // Update current time every second
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timeInterval);
  }, []);

  // Format elapsed time as HH:MM:SS
  const formatElapsedTime = useCallback((seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Format current time
  const formatCurrentTime = useCallback((date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    });
  }, []);

  // Format current date
  const formatCurrentDate = useCallback((date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'long',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }, []);

  // Start timer with state validation
  const handleStart = useCallback(() => {
    // BUG FIX: Validate state before starting
    // Prevents multiple concurrent timer intervals
    if (timerState === 'running' || timerState === 'paused') {
      console.warn('Timer already running - start prevented');
      return;
    }

    setTimerState('running');
    startTimeRef.current = Date.now() - (elapsedSeconds * 1000);

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTimeRef.current) / 1000);
      setElapsedSeconds(elapsed);
    }, 1000);
  }, [timerState, elapsedSeconds]);

  // Pause timer
  const handlePause = useCallback(() => {
    if (timerState !== 'running') return;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setTimerState('paused');
  }, [timerState]);

  // Stop timer
  const handleStop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setElapsedSeconds(0);
    setTimerState('idle');
    startTimeRef.current = null;
  }, []);

  // Resume timer
  const handleResume = useCallback(() => {
    if (timerState !== 'paused') return;

    setTimerState('running');
    startTimeRef.current = Date.now() - (elapsedSeconds * 1000);

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTimeRef.current) / 1000);
      setElapsedSeconds(elapsed);
    }, 1000);
  }, [timerState, elapsedSeconds]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <div className="timer-widget">
      <div className="timer-header">
        <Clock className="timer-icon" size={20} />
        <h3 className="timer-title">Timer</h3>
      </div>

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