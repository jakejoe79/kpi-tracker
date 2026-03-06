import React, { useState, useEffect } from 'react';
import './DashboardLayout.css';
import DailyGoalsHeader from './DailyGoalsHeader';
import ProgressBars from './ProgressBars';
import TimeRemainingWidget from './TimeRemainingWidget';
import LiveStatsPanel from './LiveStatsPanel';
import QuickActionsBar from './QuickActionsBar';
import TimerWidget from './TimerWidget';

/**
 * Main dashboard layout component
 * Displays daily goals, progress bars, time remaining, and live stats
 * Responsive design for desktop, tablet, and mobile
 * 
 * Requirements: 2.1, 2.5
 */
function DashboardLayout({ userId }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [isTablet, setIsTablet] = useState(window.innerWidth >= 768 && window.innerWidth < 1024);

  // Handle responsive design
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      setIsTablet(window.innerWidth >= 768 && window.innerWidth < 1024);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch dashboard data on mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('access_token');
        const today = new Date().toISOString().split('T')[0];
        
        // Fetch both goals and today's stats
        const [goalsRes, statsRes] = await Promise.all([
          fetch(
            `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/goals`,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            }
          ),
          fetch(
            `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/stats/today`,
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            }
          ),
        ]);

        if (!goalsRes.ok || !statsRes.ok) {
          throw new Error('Failed to fetch dashboard data');
        }

        const goalsData = await goalsRes.json();
        const statsData = await statsRes.json();
        
        // Map goals and stats data to expected structure
        const dailyGoals = goalsData.daily || {};
        setDashboardData({
          daily: {
            profit_target: dailyGoals.profit_target || 72.08,
            current_profit: dailyGoals.current_profit || statsData.profit?.current || 0,
            progress_percent: dailyGoals.progress_percent || 0,
            time_remaining_minutes: dailyGoals.time_remaining_minutes || 240,
            time_needed_minutes: dailyGoals.time_needed_minutes || 480,
            calls_needed: dailyGoals.calls_needed || 188,
            current_calls: dailyGoals.current_calls || statsData.calls?.current || 0,
            reservations_needed: dailyGoals.reservations_needed || 30,
            current_reservations: dailyGoals.current_reservations || statsData.reservations?.current || 0,
          },
          stats: statsData
        });
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Dashboard data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchDashboardData();
    }
  }, [userId]);

  // Listen for real-time updates from main dashboard
  useEffect(() => {
    const handleKpiUpdated = () => {
      console.log('kpi_updated event received in live goals dashboard, refreshing...');
      // Re-fetch dashboard data when main dashboard updates
      const fetchUpdatedData = async () => {
        try {
          const token = localStorage.getItem('access_token');
          const [goalsRes, statsRes] = await Promise.all([
            fetch(
              `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/goals`,
              {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                },
              }
            ),
            fetch(
              `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/stats/today`,
              {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                },
              }
            ),
          ]);

          if (goalsRes.ok && statsRes.ok) {
            const goalsData = await goalsRes.json();
            const statsData = await statsRes.json();
            
            const dailyGoals = goalsData.daily || {};
            setDashboardData({
              daily: {
                profit_target: dailyGoals.profit_target || 72.08,
                current_profit: dailyGoals.current_profit || statsData.profit?.current || 0,
                progress_percent: dailyGoals.progress_percent || 0,
                time_remaining_minutes: dailyGoals.time_remaining_minutes || 240,
                time_needed_minutes: dailyGoals.time_needed_minutes || 480,
                calls_needed: dailyGoals.calls_needed || 188,
                current_calls: dailyGoals.current_calls || statsData.calls?.current || 0,
                reservations_needed: dailyGoals.reservations_needed || 30,
                current_reservations: dailyGoals.current_reservations || statsData.reservations?.current || 0,
              },
              stats: statsData
            });
          }
        } catch (err) {
          console.error('Error updating dashboard data:', err);
        }
      };

      fetchUpdatedData();
    };

    window.addEventListener('kpi_updated', handleKpiUpdated);
    return () => window.removeEventListener('kpi_updated', handleKpiUpdated);
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="dashboard-error">Error: {error}</div>;
  }

  return (
    <div className={`dashboard-layout ${isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop'}`}>
      <div className="dashboard-container">
        {/* Header Section */}
        <div className="dashboard-header">
          <h1>Daily Dashboard</h1>
        </div>

        {/* Main Content Grid */}
        <div className="dashboard-content">
          {/* Goals Panel */}
          <div className="dashboard-panel goals-panel">
            <DailyGoalsHeader data={dashboardData?.daily} />
            <ProgressBars data={dashboardData?.daily} />
          </div>

          {/* Time and Stats Panel */}
          <div className="dashboard-panel stats-panel">
            <TimerWidget />
            <TimeRemainingWidget data={dashboardData?.daily} />
            <LiveStatsPanel data={dashboardData?.daily} />
          </div>
        </div>

        {/* Quick Actions Bar */}
        <div className="dashboard-actions">
          <QuickActionsBar userId={userId} onDataUpdate={() => {}} />
        </div>
      </div>
    </div>
  );
}

export default DashboardLayout;
