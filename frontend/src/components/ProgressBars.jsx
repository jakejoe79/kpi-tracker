import React from 'react';
import './ProgressBars.css';

/**
 * Progress Bars Component
 * Displays three progress bars for profit, calls, and reservations
 * Real-time percentage display with smooth animations
 * Color-coded based on progress (green/yellow/red)
 * 
 * Requirements: 2.1, 2.2
 */
function ProgressBars({ data }) {
  if (!data) {
    return <div className="progress-bars-empty">No progress data available</div>;
  }

  const calculateProgress = (current, target) => {
    if (target === 0) return 0;
    return Math.min((current / target) * 100, 100);
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 75) return 'green';
    if (percentage >= 50) return 'yellow';
    return 'red';
  };

  const profitProgress = calculateProgress(data.current_profit || 0, data.profit_target || 1);
  const callsProgress = calculateProgress(data.current_calls || 0, data.calls_needed || 1);
  const reservationsProgress = calculateProgress(
    data.current_reservations || 0,
    data.reservations_needed || 1
  );

  const profitColor = getProgressColor(profitProgress);
  const callsColor = getProgressColor(callsProgress);
  const reservationsColor = getProgressColor(reservationsProgress);

  const ProgressBar = ({ label, current, target, progress, color }) => (
    <div className="progress-bar-container">
      <div className="progress-bar-header">
        <span className="progress-bar-label">{label}</span>
        <span className="progress-bar-percentage">{Math.round(progress)}%</span>
      </div>
      <div className="progress-bar-track">
        <div
          className={`progress-bar-fill color-${color}`}
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label={`${label}: ${Math.round(progress)}% complete`}
        />
      </div>
      <div className="progress-bar-info">
        <span className="progress-bar-current">{current}</span>
        <span className="progress-bar-target">/ {target}</span>
      </div>
    </div>
  );

  return (
    <div className="progress-bars">
      <h3 className="progress-bars-title">Progress</h3>
      <div className="progress-bars-list">
        <ProgressBar
          label="Profit"
          current={`$${(data.current_profit || 0).toFixed(2)}`}
          target={`$${(data.profit_target || 0).toFixed(2)}`}
          progress={profitProgress}
          color={profitColor}
        />
        <ProgressBar
          label="Calls"
          current={data.current_calls || 0}
          target={data.calls_needed || 0}
          progress={callsProgress}
          color={callsColor}
        />
        <ProgressBar
          label="Reservations"
          current={data.current_reservations || 0}
          target={data.reservations_needed || 0}
          progress={reservationsProgress}
          color={reservationsColor}
        />
      </div>
    </div>
  );
}

export default ProgressBars;
