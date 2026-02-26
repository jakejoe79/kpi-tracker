import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Award } from 'lucide-react';

function ForecastDashboard({ forecast, signals }) {
  if (!forecast) return <div>Loading forecast...</div>;

  const getRiskColor = (level) => {
    if (level === 'red' || level === 'high') return '#ef4444';
    if (level === 'yellow' || level === 'medium') return '#f59e0b';
    return '#22c55e';
  };
  
  const getRiskTierBadge = (riskTier, riskScore) => {
    const tier = riskTier || getRiskTierLabel(riskScore);
    const colors = {
      '🔴 High Risk': { bg: '#fef2f2', border: '#ef4444', text: '#991b1b' },
      '🟡 Medium Risk': { bg: '#fffbeb', border: '#f59e0b', text: '#92400e' },
      '🟢 Low Risk': { bg: '#f0fdf4', border: '#22c55e', text: '#166534' }
    };
    const style = colors[tier] || colors['🟢 Low Risk'];
    return { tier, style };
  };
  
  const getRiskTierLabel = (score) => {
    if (score >= 70) return '🔴 High Risk';
    if (score >= 40) return '🟡 Medium Risk';
    return '🟢 Low Risk';
  };

  const formatNumber = (num) => {
    return typeof num === 'number' ? num.toFixed(1) : num;
  };

  // Split signals into momentum (positive) and risk (negative)
  // ELITE RULE: Never show more than 5 total
  const momentumSignals = (signals?.filter(s => s.signal_type === 'momentum') || []).slice(0, 2);
  const riskSignals = (signals?.filter(s => s.signal_type === 'risk') || []).slice(0, 3);
  
  // Ensure total never exceeds 5
  const totalSignals = momentumSignals.length + riskSignals.length;
  const displayMomentum = totalSignals > 5 ? momentumSignals.slice(0, 2) : momentumSignals;
  const displayRisk = totalSignals > 5 ? riskSignals.slice(0, 3) : riskSignals;

  return (
    <div>

      {/* STRATEGIC LAYER: TEAM HEALTH CARD - Answers "Are we hitting our number?" */}
      <div className="card" style={{ marginBottom: '1.5rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: `4px solid ${forecast.risk_indicator === '🔴' ? '#ef4444' : forecast.risk_indicator === '🟡' ? '#f59e0b' : '#22c55e'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ color: 'white', margin: 0, fontSize: '1.5rem' }}>
            {forecast.risk_indicator} Team Performance Forecast
          </h3>
          <div style={{ fontSize: '2rem' }}>
            {forecast.trend_direction}
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '1rem',
          marginBottom: '1rem'
        }}>
          <div style={{ background: 'rgba(255,255,255,0.15)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.9, marginBottom: '0.25rem' }}>Current</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              {formatNumber(forecast.team_current_reservations)}
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.15)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.9, marginBottom: '0.25rem' }}>Projected</div>
            <div
              style={{
                fontSize: '2rem',
                fontWeight: 'bold',
                color: forecast.team_gap >= 0 ? '#4ade80' : '#fca5a5'
              }}
            >
              {formatNumber(forecast.team_projected_reservations)}
            </div>
            <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>{formatNumber(forecast.percent_of_goal)}% of goal</div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.15)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.9, marginBottom: '0.25rem' }}>Gap</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: forecast.team_gap >= 0 ? '#4ade80' : '#fca5a5' }}>
              {forecast.team_gap > 0 ? '+' : ''}{formatNumber(forecast.team_gap)}
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.15)', padding: '1rem', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.9, marginBottom: '0.25rem' }}>Required Daily</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              {formatNumber(forecast.required_daily_rate)}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '6px' }}>
          <div>
            <strong>Days Elapsed:</strong> {forecast.days_elapsed}
          </div>
          <div>
            <strong>Days Remaining:</strong> {forecast.days_remaining}
          </div>
          <div>
            <strong>Confidence:</strong> {forecast.confidence}
          </div>
          <div>
            <strong>Trend:</strong> {forecast.trend_direction} {forecast.trend_direction === '↑' ? 'Improving' : forecast.trend_direction === '↓' ? 'Declining' : 'Stable'}
          </div>
        </div>
      </div>

      {/* TACTICAL LAYER: TOP 5 SIGNALS - Answers "Who do I talk to right now?" */}
      <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#18181b', borderRadius: '8px', border: '1px solid #27272a' }}>
        <h4 style={{ margin: 0, fontSize: '0.875rem', color: '#a1a1aa', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          ⚡ Top 5 Intervention Signals - Sorted by Risk Score
        </h4>
      </div>

      {/* MOMENTUM SECTION - Green */}
      <div className="card" style={{ marginBottom: '1.5rem', background: '#f0fdf4', borderLeft: '4px solid #22c55e' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#15803d' }}>
          <TrendingUp size={24} /> 🟢 Momentum - Top Performers
        </h3>
        <p style={{ fontSize: '0.875rem', color: '#166534', marginBottom: '1rem' }}>
          Projected to exceed quota • Most improved conversion this period
        </p>

        {displayMomentum.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
            No momentum signals yet - keep pushing!
          </div>
        ) : (
          displayMomentum.map((signal, idx) => (
            <div
              key={signal.user_id || idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem',
                marginBottom: '0.75rem',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #bbf7d0'
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <Award size={18} color="#22c55e" />
                  <strong style={{ fontSize: '1.1rem' }}>#{signal.rank} {signal.user_id}</strong>
                </div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Projected: <strong>{formatNumber(signal.projected_reservations)}</strong> ({signal.projected_percent_of_goal}% of goal) | 
                  Gap: <strong style={{ color: signal.gap >= 0 ? '#22c55e' : '#ef4444' }}>{signal.gap > 0 ? '+' : ''}{formatNumber(signal.gap)}</strong> | 
                  Trend: {signal.trend_direction} {signal.trend}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                  Confidence: <strong>{signal.confidence_level}</strong> | Priority: <strong>#{signal.operational_priority}</strong>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem' }}>
                  ✓ {signal.action_required}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                {signal.risk_tier && (
                  <div
                    style={{
                      background: getRiskTierBadge(signal.risk_tier, signal.risk_score).style.bg,
                      border: `2px solid ${getRiskTierBadge(signal.risk_tier, signal.risk_score).style.border}`,
                      color: getRiskTierBadge(signal.risk_tier, signal.risk_score).style.text,
                      padding: '0.5rem 1rem',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                      marginBottom: '0.5rem'
                    }}
                  >
                    {signal.risk_tier}
                  </div>
                )}
                {!signal.can_alert && (
                  <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.25rem' }}>
                    ⏳ Alert cooldown active
                  </div>
                )}
                {signal.has_significant_change && (
                  <div style={{ fontSize: '0.65rem', color: '#22c55e', marginTop: '0.25rem' }}>
                    ⚡ Significant change detected
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* RISK SECTION - Red */}
      <div className="card" style={{ background: '#fef2f2', borderLeft: '4px solid #ef4444' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#991b1b' }}>
          <AlertTriangle size={24} /> 🔴 Risk - Needs Attention
        </h3>
        <p style={{ fontSize: '0.875rem', color: '#991b1b', marginBottom: '1rem' }}>
          Largest projected deficits • Lowest conversion efficiency • Max 5 signals total
        </p>

        {displayRisk.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: '#6b7280' }}>
            No risk signals - team is performing well!
          </div>
        ) : (
          displayRisk.map((signal, idx) => (
            <div
              key={signal.user_id || idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem',
                marginBottom: '0.75rem',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #fecaca'
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <TrendingDown size={18} color="#ef4444" />
                  <strong style={{ fontSize: '1.1rem' }}>#{signal.rank} {signal.user_id}</strong>
                </div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Projected: <strong>{formatNumber(signal.projected_reservations)}</strong> ({signal.projected_percent_of_goal}% of goal) | 
                  Gap: <strong style={{ color: '#ef4444' }}>{formatNumber(signal.gap)}</strong> | 
                  Trend: {signal.trend_direction} {signal.trend}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                  Confidence: <strong>{signal.confidence_level}</strong> | Priority: <strong>#{signal.operational_priority}</strong>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#dc2626', marginTop: '0.25rem', fontWeight: '600' }}>
                  ⚠️ {signal.action_required}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                {signal.risk_tier && (
                  <div
                    style={{
                      background: getRiskTierBadge(signal.risk_tier, signal.risk_score).style.bg,
                      border: `2px solid ${getRiskTierBadge(signal.risk_tier, signal.risk_score).style.border}`,
                      color: getRiskTierBadge(signal.risk_tier, signal.risk_score).style.text,
                      padding: '0.5rem 1rem',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                      marginBottom: '0.5rem'
                    }}
                  >
                    {signal.risk_tier}
                  </div>
                )}
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                  Risk Score: {formatNumber(signal.risk_score)}
                </div>
                {!signal.can_alert && (
                  <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.25rem' }}>
                    ⏳ Alert cooldown active
                  </div>
                )}
                {signal.has_significant_change && (
                  <div style={{ fontSize: '0.65rem', color: '#ef4444', marginTop: '0.25rem' }}>
                    ⚡ Significant change detected
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
}

export default ForecastDashboard;