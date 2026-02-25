import React from 'react';

function ForecastDashboard({ forecast, signals }) {
  if (!forecast) return <div>Loading forecast...</div>;

  const getRiskColor = (level) => {
    if (level === 'red' || level === 'high') return '#ef4444';
    if (level === 'yellow' || level === 'medium') return '#f59e0b';
    return '#22c55e';
  };

  const formatNumber = (num) => {
    return typeof num === 'number' ? num.toFixed(1) : num;
  };

  return (
    <div>

      {/* TEAM FORECAST CARD */}
      <div className="card" style={{ marginBottom: '1.5rem', background: '#f0f9ff' }}>
        <h3>Team Forecast</h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1rem'
        }}>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              {formatNumber(forecast.team_current_reservations)}
            </div>
            <div>Current Reservations</div>
          </div>

          <div>
            <div
              style={{
                fontSize: '2rem',
                fontWeight: 'bold',
                color: forecast.team_gap >= 0 ? '#22c55e' : '#ef4444'
              }}
            >
              {formatNumber(forecast.team_projected_reservations)}
            </div>
            <div>Projected ({formatNumber(forecast.percent_of_goal)}% of goal)</div>
          </div>

          <div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              {formatNumber(forecast.required_daily_rate)}
            </div>
            <div>Required Daily Rate</div>
          </div>
        </div>

        <div style={{ marginTop: '1rem' }}>
          <strong>Gap:</strong> {forecast.team_gap > 0 ? '+' : ''}{formatNumber(forecast.team_gap)} | 
          <strong> Confidence:</strong> {forecast.confidence} | 
          <strong> Days Remaining:</strong> {forecast.days_remaining}
        </div>
      </div>

      {/* TOP 5 SIGNALS */}
      <div className="card">
        <h3>Top 5 Intervention Signals</h3>

        {!signals || signals.length === 0 ? (
          <div>No signals available</div>
        ) : (
          signals.map((signal, idx) => (
            <div
              key={signal.user_id || idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.75rem',
                marginBottom: '0.5rem',
                background: getRiskColor(signal.risk_level) + '20',
                borderLeft: `4px solid ${getRiskColor(signal.risk_level)}`
              }}
            >
              <div>
                <strong>#{idx + 1} {signal.user_id}</strong>

                <div style={{ fontSize: '0.875rem' }}>
                  Projected: {formatNumber(signal.projected_reservations)} | 
                  Gap: {signal.gap > 0 ? '+' : ''}{formatNumber(signal.gap)} | 
                  Trend: {signal.trend}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div
                  style={{
                    background: getRiskColor(signal.risk_level),
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}
                >
                  {signal.risk_level?.toUpperCase()}
                </div>

                <div style={{ fontSize: '0.75rem' }}>
                  Risk: {formatNumber(signal.risk_score)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
}

export default ForecastDashboard;