import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import './TimerWidget.css';

/**
 * Simple Clock Widget
 * Shows current time and date
 * Timestamp is captured when booking/reservation is added
 */
function TimerWidget() {
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Format current time as HH:MM:SS
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    });
  };

  // Format current date
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="timer-widget">
      <div className="timer-header">
        <Clock className="timer-icon" size={20} />
        <h3 className="timer-title">Time</h3>
      </div>

      {/* Current Time Display */}
      <div className="timer-current-time">
        <div className="current-time-value">{formatTime(currentTime)}</div>
        <div className="current-date-value">{formatDate(currentTime)}</div>
      </div>

      {/* Timestamp capture note */}
      <div className="timer-note">
        <span className="note-text">Timestamp captured on booking</span>
      </div>
    </div>
  );
}

export default TimerWidget;
