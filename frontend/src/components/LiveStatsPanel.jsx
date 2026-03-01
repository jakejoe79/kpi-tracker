import React from 'react';
import './LiveStatsPanel.css';

/**
 * Live Stats Panel Component
 * Displays real-time stats: calls, bookings, profit, time worked
 * Shows conversion rate and average profit per booking
 * Updates as user logs entries
 * 
 * Requirements: 2.8
 */
function LiveStatsPanel({ data }) {
  if (!data) {
    return <div className="live-stats-empty">No stats data available</div>;
  }

  const calculateConversionRate = () => {
    const calls = data.current_calls || 0;
    if (calls === 0) return 0;
    const bookings = data.current_reservations || 0;
    return ((bookings / calls) * 100).toFixed(1);
  };

  const calculateAvgProfitPerBooking = () => {
    const bookings = data.current_reservations || 0;
    if (bookings === 0) return 0;
    const profit = data.current_profit || 0;
    return (profit / bookings).toFixed(2);
  };

  const formatTime = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const StatItem = ({ label, value, unit = '' }) => (
    <div className="stat-item">
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {value}
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
    </div>
  );

  return (
    <div className="live-stats-panel">
      <h3 className="live-stats-title">Live Stats</h3>

      <div className="stats-grid">
        <StatItem
          label="Calls Received"
          value={data.current_calls || 0}
        />
        <StatItem
          label="Bookings"
          value={data.current_reservations || 0}
        />
        <StatItem
          label="Profit"
          value={`$${(data.current_profit || 0).toFixed(2)}`}
        />
        <StatItem
          label="Time Worked"
          value={formatTime(data.total_time_minutes || 0)}
        />
        <StatItem
          label="Conversion Rate"
          value={calculateConversionRate()}
          unit="%"
        />
        <StatItem
          label="Avg Profit/Booking"
          value={`$${calculateAvgProfitPerBooking()}`}
        />
      </div>
    </div>
  );
}

export default LiveStatsPanel;
