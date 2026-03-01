import React from 'react';
import './DailyGoalsHeader.css';

/**
 * Daily Goals Header Component
 * Displays profit target, calls needed, and reservations needed
 * Shows current progress for each metric with color-coded status
 * 
 * Requirements: 2.1
 */
function DailyGoalsHeader({ data }) {
  if (!data) {
    return <div className="goals-header-empty">No goals data available</div>;
  }

  const getStatusColor = (current, target) => {
    if (target === 0) return 'neutral';
    const percentage = (current / target) * 100;
    if (percentage >= 75) return 'green';
    if (percentage >= 50) return 'yellow';
    return 'red';
  };

  const profitStatus = getStatusColor(data.current_profit || 0, data.profit_target || 1);
  const callsStatus = getStatusColor(data.current_calls || 0, data.calls_needed || 1);
  const reservationsStatus = getStatusColor(
    data.current_reservations || 0,
    data.reservations_needed || 1
  );

  return (
    <div className="goals-header">
      <h2 className="goals-header-title">Daily Goals</h2>
      
      <div className="goals-grid">
        {/* Profit Target */}
        <div className={`goal-card status-${profitStatus}`}>
          <div className="goal-label">Profit Target</div>
          <div className="goal-target">${(data.profit_target || 0).toFixed(2)}</div>
          <div className="goal-current">
            Current: <span className="goal-value">${(data.current_profit || 0).toFixed(2)}</span>
          </div>
          <div className="goal-status-indicator" aria-label={`Profit status: ${profitStatus}`} />
        </div>

        {/* Calls Needed */}
        <div className={`goal-card status-${callsStatus}`}>
          <div className="goal-label">Calls Needed</div>
          <div className="goal-target">{data.calls_needed || 0}</div>
          <div className="goal-current">
            Current: <span className="goal-value">{data.current_calls || 0}</span>
          </div>
          <div className="goal-status-indicator" aria-label={`Calls status: ${callsStatus}`} />
        </div>

        {/* Reservations Needed */}
        <div className={`goal-card status-${reservationsStatus}`}>
          <div className="goal-label">Reservations Needed</div>
          <div className="goal-target">{data.reservations_needed || 0}</div>
          <div className="goal-current">
            Current: <span className="goal-value">{data.current_reservations || 0}</span>
          </div>
          <div className="goal-status-indicator" aria-label={`Reservations status: ${reservationsStatus}`} />
        </div>
      </div>
    </div>
  );
}

export default DailyGoalsHeader;
