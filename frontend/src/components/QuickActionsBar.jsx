import React, { useState } from 'react';
import './QuickActionsBar.css';

/**
 * Quick Actions Bar Component
 * Provides quick access to add bookings, spins, and income
 * Includes timer controls (start/stop/pause)
 * 
 * Requirements: 2.6, 2.7
 */
function QuickActionsBar({ userId, onDataUpdate }) {
  const [timerRunning, setTimerRunning] = useState(false);
  const [timerPaused, setTimerPaused] = useState(false);

  const handleAddBooking = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/entries/today/bookings`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            profit: 0,
            notes: 'Quick add',
          }),
        }
      );

      if (response.ok) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('Error adding booking:', error);
    }
  };

  const handleAddSpin = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/entries/today/spins`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            notes: 'Quick add',
          }),
        }
      );

      if (response.ok) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('Error adding spin:', error);
    }
  };

  const handleAddIncome = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/entries/today/income`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            amount: 0,
            notes: 'Quick add',
          }),
        }
      );

      if (response.ok) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('Error adding income:', error);
    }
  };

  const handleTimerStart = () => {
    setTimerRunning(true);
    setTimerPaused(false);
  };

  const handleTimerPause = () => {
    setTimerPaused(!timerPaused);
  };

  const handleTimerStop = () => {
    setTimerRunning(false);
    setTimerPaused(false);
  };

  return (
    <div className="quick-actions-bar">
      <div className="actions-group">
        <h3 className="actions-title">Quick Actions</h3>
        <div className="actions-buttons">
          <button
            className="action-button action-booking"
            onClick={handleAddBooking}
            aria-label="Add booking"
            title="Add a new booking"
          >
            <span className="action-icon">📅</span>
            <span className="action-label">Add Booking</span>
          </button>

          <button
            className="action-button action-spin"
            onClick={handleAddSpin}
            aria-label="Add spin"
            title="Add a new spin"
          >
            <span className="action-icon">🎯</span>
            <span className="action-label">Add Spin</span>
          </button>

          <button
            className="action-button action-income"
            onClick={handleAddIncome}
            aria-label="Add income"
            title="Add misc income"
          >
            <span className="action-icon">💰</span>
            <span className="action-label">Add Income</span>
          </button>
        </div>
      </div>

      <div className="timer-group">
        <h3 className="timer-title">Timer</h3>
        <div className="timer-buttons">
          <button
            className={`timer-button timer-start ${timerRunning ? 'active' : ''}`}
            onClick={handleTimerStart}
            disabled={timerRunning}
            aria-label="Start timer"
            title="Start the timer"
          >
            ▶ Start
          </button>

          <button
            className={`timer-button timer-pause ${timerPaused ? 'active' : ''}`}
            onClick={handleTimerPause}
            disabled={!timerRunning}
            aria-label="Pause timer"
            title="Pause the timer"
          >
            ⏸ {timerPaused ? 'Resume' : 'Pause'}
          </button>

          <button
            className="timer-button timer-stop"
            onClick={handleTimerStop}
            disabled={!timerRunning}
            aria-label="Stop timer"
            title="Stop the timer"
          >
            ⏹ Stop
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuickActionsBar;
