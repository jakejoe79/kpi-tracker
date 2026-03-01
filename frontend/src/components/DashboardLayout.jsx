import React, { useState, useEffect } from 'react';
import './DashboardLayout.css';
import DailyGoalsHeader from './DailyGoalsHeader';
import ProgressBars from './ProgressBars';
import TimeRemainingWidget from './TimeRemainingWidget';
import LiveStatsPanel from './LiveStatsPanel';
import QuickActionsBar from './QuickActionsBar';

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
        const response = await fetch(
          `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/goals/current`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }

        const data = await response.json();
        setDashboardData(data);
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
