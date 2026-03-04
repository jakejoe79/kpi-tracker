import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Clock } from 'lucide-react';
import './TimerWidget.css';

/**
 * Simple Clock Widget
 * Shows current time and date
 * Timestamp is captured when booking/reservation is added
 */
function TimerWidget() {
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

  // Start timer
  const handleStart = () => {
    setTimerState('running');
    startTimeRef.current = Date.now() - (elapsedSeconds * 1000);

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTimeRef.current) / 1000);
      setElapsedSeconds(elapsed);
    }, 1000);
  };

  // Pause timer
  const handlePause = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setTimerState('paused');
  };

  // Stop timer
  const handleStop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setElapsedSeconds(0);
    setTimerState('idle');
    startTimeRef.current = null;
  };

  // Resume timer
  const handleResume = () => {
    setTimerState('running');
    startTimeRef.current = Date.now() - (elapsedSeconds * 1000);

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTimeRef.current) / 1000);
      setElapsedSeconds(elapsed);
    }, 1000);
  };

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
        <h3 className="timer-title">Time</h3>
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
