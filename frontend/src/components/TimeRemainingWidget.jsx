import React, { useState, useEffect } from 'react';
import './TimeRemainingWidget.css';

/**
 * Time Remaining Widget Component
 * Displays time remaining to reach daily target
 * Shows pace indicator (ON TRACK / MODERATE / BEHIND)
 * Updates every minute
 * 
 * Requirements: 2.3, 2.4, 2.10
 */
function TimeRemainingWidget({ data }) {
  const [displayTime, setDisplayTime] = useState('');
  const [paceStatus, setPaceStatus] = useState('neutral');

  useEffect(() => {
    const updateDisplay = () => {
      if (!data) {
        setDisplayTime('--:--');
        setPaceStatus('neutral');
        return;
      }

      const timeRemaining = data.time_remaining_minutes || 0;
      const hours = Math.floor(timeRemaining / 60);
      const minutes = timeRemaining % 60;

      setDisplayTime(`${hours}h ${minutes}m`);

      // Calculate pace indicator based on progress
      const profitProgress = data.profit_target
        ? (data.current_profit / data.profit_target) * 100
        : 0;
      const callsProgress = data.calls_needed
        ? (data.current_calls / data.calls_needed) * 100
        : 0;
      const reservationsProgress = data.reservations_needed
        ? (data.current_reservations / data.reservations_needed) * 100
        : 0;

      // Average progress across all metrics
      const avgProgress = (profitProgress + callsProgress + reservationsProgress) / 3;

      if (avgProgress >= 75) {
        setPaceStatus('on-track');
      } else if (avgProgress >= 50) {
        setPaceStatus('moderate');
      } else {
        setPaceStatus('behind');
      }
    };

    updateDisplay();

    // Update every minute
    const interval = setInterval(updateDisplay, 60000);

    return () => clearInterval(interval);
  }, [data]);

  if (!data) {
    return <div className="time-remaining-empty">No time data available</div>;
  }

  const getPaceLabel = () => {
    switch (paceStatus) {
      case 'on-track':
        return 'ON TRACK ✓';
      case 'moderate':
        return 'MODERATE';
      case 'behind':
        return 'BEHIND ⚠';
      default:
        return 'NEUTRAL';
    }
  };

  const getPaceIcon = () => {
    switch (paceStatus) {
      case 'on-track':
        return '✓';
      case 'moderate':
        return '◐';
      case 'behind':
        return '⚠';
      default:
        return '○';
    }
  };

  return (
    <div className={`time-remaining-widget status-${paceStatus}`}>
      <div className="time-remaining-header">
        <h3 className="time-remaining-title">Time Remaining</h3>
        <span className="time-remaining-icon">{getPaceIcon()}</span>
      </div>

      <div className="time-remaining-display">
        <div className="time-remaining-value">⏱ {displayTime}</div>
        <div className="time-remaining-label">to reach daily target</div>
      </div>

      <div className="time-remaining-pace">
        <span className={`pace-indicator pace-${paceStatus}`}>
          Pace: {getPaceLabel()}
        </span>
      </div>

      {paceStatus === 'behind' && (
        <div className="time-remaining-warning">
          You're behind pace. Consider increasing your activity to catch up.
        </div>
      )}
    </div>
  );
}

export default TimeRemainingWidget;
