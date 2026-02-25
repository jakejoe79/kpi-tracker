
# Create complete frontend App.js

frontend_app_js = '''import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import DataEntry from './components/DataEntry';
import History from './components/History';
import Settings, { getStoredSettings } from './components/Settings';
import { LayoutDashboard, Plus, Clock, Settings as SettingsIcon } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'https://kpi-tracker-88dy.onrender.com';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [todayEntry, setTodayEntry] = useState(null);
  const [periodInfo, setPeriodInfo] = useState(null);
  const [goals, setGoals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [customSettings, setCustomSettings] = useState(getStoredSettings());

  // SHARED TIMER STATE
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const timerRef = useRef(null);

  // Keep backend alive - ping every 10 minutes
  useEffect(() => {
    const BACKEND_URL = API_URL;
    
    fetch(`${BACKEND_URL}/api/health`).catch(() => {});
    
    const interval = setInterval(() => {
      fetch(`${BACKEND_URL}/api/health`).catch(() => {});
      console.log('Pinged backend to keep alive');
    }, 600000);
    
    return () => clearInterval(interval);
  }, []);

  // Load timer from localStorage on mount
  useEffect(() => {
    const savedTimer = localStorage.getItem('kpi_timer');
    if (savedTimer) {
      const { seconds, running, paused, timestamp } = JSON.parse(savedTimer);
      const elapsed = Math.floor((Date.now() - timestamp) / 1000);
      setTimerSeconds(seconds + (running && !paused ? elapsed : 0));
      setIsTimerRunning(running);
      setIsPaused(paused);
    }
  }, []);

  // Save timer to localStorage
  useEffect(() => {
    localStorage.setItem('kpi_timer', JSON.stringify({
      seconds: timerSeconds,
      running: isTimerRunning,
      paused: isPaused,
      timestamp: Date.now()
    }));
  }, [timerSeconds, isTimerRunning, isPaused]);

  // Timer tick
  useEffect(() => {
    if (isTimerRunning && !isPaused) {
      timerRef.current = setInterval(() => {
        setTimerSeconds(s => s + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isTimerRunning, isPaused]);

  // Fetch data on mount
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsRes, entryRes, periodRes, goalsRes] = await Promise.all([
        fetch(`${API_URL}/api/stats/biweekly`),
        fetch(`${API_URL}/api/entries/today`),
        fetch(`${API_URL}/api/periods/current`),
        fetch(`${API_URL}/api/goals`)
      ]);

      if (!statsRes.ok || !entryRes.ok || !periodRes.ok || !goalsRes.ok) {
        throw new Error('Failed to fetch data');
      }

      setStats(await statsRes.json());
      setTodayEntry(await entryRes.json());
      setPeriodInfo(await periodRes.json());
      
      // Get goals from API (now reads from database)
      const apiGoals = await goalsRes.json();
      setGoals(apiGoals);
      
      // Also update localStorage for offline access
      localStorage.setItem('kpi_goals', JSON.stringify(apiGoals));
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message);
      
      // Fallback to localStorage if API fails
      const savedGoals = localStorage.getItem('kpi_goals');
      if (savedGoals) {
        setGoals(JSON.parse(savedGoals));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSettingsChange = async (newSettings) => {
    setCustomSettings(newSettings);
    
    // Save to localStorage
    localStorage.setItem('kpi_goals', JSON.stringify(newSettings.goals));
    localStorage.setItem('kpi_conversion', JSON.stringify(newSettings.conversion));
    
    // ALSO save to backend API
    try {
      const response = await fetch(`${API_URL}/api/goals`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings.goals)
      });
      
      if (response.ok) {
        console.log('Goals saved to backend');
        // Refresh goals from backend to confirm
        const goalsRes = await fetch(`${API_URL}/api/goals`);
        if (goalsRes.ok) {
          const updatedGoals = await goalsRes.json();
          setGoals(updatedGoals);
        }
      } else {
        console.error('Failed to save goals to backend');
      }
    } catch (err) {
      console.error('Error saving goals:', err);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const renderContent = () => {
    if (loading) return <div className="loading">Loading...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    switch (activeTab) {
      case 'dashboard':
        return <Dashboard stats={stats} goals={goals} periodInfo={periodInfo} />;
      case 'entry':
        return (
          <DataEntry
            todayEntry={todayEntry}
            onUpdate={fetchData}
            timerSeconds={timerSeconds}
            isTimerRunning={isTimerRunning}
            isPaused={isPaused}
            onTimerToggle={() => {
              if (isTimerRunning) {
                setIsPaused(!isPaused);
              } else {
                setIsTimerRunning(true);
                setIsPaused(false);
              }
            }}
            onTimerReset={() => {
              setTimerSeconds(0);
              setIsTimerRunning(false);
              setIsPaused(false);
            }}
            formatTime={formatTime}
          />
        );
      case 'history':
        return <History />;
      case 'settings':
        return <Settings onSettingsChange={handleSettingsChange} />;
      default:
        return <Dashboard stats={stats} goals={goals} periodInfo={periodInfo} />;
    }
  };

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-brand">KPI Tracker</div>
        <div className="nav-tabs">
          <button
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} /> Dashboard
          </button>
          <button
            className={activeTab === 'entry' ? 'active' : ''}
            onClick={() => setActiveTab('entry')}
          >
            <Plus size={18} /> Data Entry
          </button>
          <button
            className={activeTab === 'history' ? 'active' : ''}
            onClick={() => setActiveTab('history')}
          >
            <Clock size={18} /> History
          </button>
          <button
            className={activeTab === 'settings' ? 'active' : ''}
            onClick={() => setActiveTab('settings')}
          >
            <SettingsIcon size={18} /> Settings
          </button>
        </div>
      </nav>
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
'''

print("FRONTEND App.js READY")
print("=" * 50)
print(f"Length: {len(frontend_app_js)} characters")
print("\nKey changes:")
print("1. Fetches goals from API on load")
print("2. Saves goals to API when settings change")
print("3. Refreshes goals from backend after save")
print("4. Falls back to localStorage if API fails")
