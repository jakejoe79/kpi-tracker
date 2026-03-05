import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import {
  Phone, Calendar, DollarSign, Star, Clock, TrendingUp,
  Plus, Trash2, Play, Square, Download, Settings, X, Loader2,
  RefreshCw, ChevronDown, ChevronUp, Zap, Lock, BarChart3
} from 'lucide-react';
import ForecastDashboard from './ForecastDashboard';
import { GoalDisplay } from './components/GoalDisplay';
import { useRealtimePolling } from './hooks/use-realtime-polling';
import StatsDashboard from './StatsDashboard';
import SettingsPanel from './settings';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${API_URL}/api`;

// Helper to get current auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

// =============================================================================
// COMPONENTS
// =============================================================================

const StatCard = ({ title, icon: Icon, current, goal, diff, status, isMoney = false, suffix = '' }) => {
  const isAhead = status === 'ahead';
  const statusColor = isAhead ? '#22C55E' : '#EF4444';
  const diffText = isMoney 
    ? `${diff >= 0 ? '+' : ''}$${Math.abs(diff).toFixed(2)}`
    : `${diff >= 0 ? '+' : ''}${diff}`;
  
  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800" data-testid={`stat-${title.toLowerCase()}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={16} className="text-zinc-500" />
        <span className="text-xs uppercase tracking-wider text-zinc-500 font-medium">{title}</span>
      </div>
      <div className="text-3xl font-bold text-white">
        {isMoney ? `$${current.toFixed(2)}` : current}{suffix}
      </div>
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-zinc-500">
          Goal: {isMoney ? `$${goal.toFixed(2)}` : goal}{suffix}
        </span>
        <span 
          className="text-sm font-bold px-2 py-0.5 rounded"
          style={{ 
            backgroundColor: `${statusColor}20`,
            color: statusColor 
          }}
        >
          {isAhead ? 'Ahead' : 'Behind'} {Math.abs(diff)}{isMoney ? '' : ''}{suffix ? '' : (isMoney ? '' : '')}
        </span>
      </div>
    </div>
  );
};

const EarningsCard = ({ title, usd, pesos, pesoRate, showPesos = true }) => (
  <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 rounded-xl p-4 border border-zinc-800">
    <h3 className="text-sm font-semibold text-zinc-400 mb-3">{title}</h3>
    <div className="space-y-2">
      <div className="flex justify-between">
        <span className="text-zinc-500">Profit</span>
        <span className="text-white font-medium">${usd.profit.toFixed(2)}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-zinc-500">Spins</span>
        <span className="text-white font-medium">${usd.spins.toFixed(2)}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-zinc-500">Misc</span>
        <span className="text-white font-medium">${usd.misc.toFixed(2)}</span>
      </div>
      <div className="border-t border-zinc-800 pt-2 flex justify-between">
        <span className="text-zinc-400 font-semibold">Total USD</span>
        <span className="text-emerald-400 font-bold text-lg">${usd.total.toFixed(2)}</span>
      </div>
      {showPesos && (
        <>
          <div className="border-t border-zinc-800 pt-2 mt-2">
            <div className="flex justify-between text-xs text-zinc-500 mb-1">
              <span>Rate: {pesoRate} MXN/USD</span>
              <span>Gross: ${pesos.gross_pesos.toFixed(2)} MXN</span>
            </div>
            <div className="flex justify-between text-xs text-zinc-500 mb-1">
              <span>Service Fee (17%)</span>
              <span>-${pesos.service_fee.toFixed(2)} MXN</span>
            </div>
            {pesos.payday_deduction > 0 && (
              <div className="flex justify-between text-xs text-zinc-500 mb-1">
                <span>Payday Deduction</span>
                <span>-${pesos.payday_deduction.toFixed(2)} MXN</span>
              </div>
            )}
            <div className="flex justify-between mt-2">
              <span className="text-zinc-400 font-semibold">Net Pesos</span>
              <span className="text-amber-400 font-bold text-lg">${pesos.net_pesos.toFixed(2)} MXN</span>
            </div>
          </div>
        </>
      )}
    </div>
  </div>
);

const SimpleClock = () => {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date());
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  const formatTime = (date) => {
    const hrs = date.getHours().toString().padStart(2, '0');
    const mins = date.getMinutes().toString().padStart(2, '0');
    const secs = date.getSeconds().toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
  };
  
  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <div className="flex items-center gap-2 mb-3">
        <Clock size={18} className="text-zinc-500" />
        <span className="text-sm font-semibold text-zinc-400">Current Time</span>
      </div>
      <div className="text-4xl font-mono font-bold text-white text-center my-4">
        {formatTime(time)}
      </div>
      <p className="text-xs text-zinc-500 text-center">
        Time is captured when you add a booking
      </p>
    </div>
  );
};

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-zinc-900 rounded-t-2xl md:rounded-2xl w-full max-w-md max-h-[90vh] overflow-auto border border-zinc-800">
        <div className="sticky top-0 bg-zinc-900 border-b border-zinc-800 p-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">{title}</h2>
          <button onClick={onClose} className="p-2 hover:bg-zinc-800 rounded-lg" data-testid="modal-close">
            <X size={20} className="text-zinc-400" />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
};

const Input = ({ label, ...props }) => (
  <div className="mb-4">
    {label && <label className="block text-sm text-zinc-400 mb-2">{label}</label>}
    <input
      className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:border-orange-500 focus:outline-none"
      {...props}
    />
  </div>
);

const Toggle = ({ label, checked, onChange }) => (
  <div className="flex items-center justify-between mb-4">
    <span className="text-sm text-zinc-400">{label}</span>
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`w-12 h-6 rounded-full transition-colors ${checked ? 'bg-orange-500' : 'bg-zinc-700'}`}
    >
      <div className={`w-5 h-5 bg-white rounded-full transition-transform ${checked ? 'translate-x-6' : 'translate-x-0.5'}`} />
    </button>
  </div>
);

const ProBadge = () => (
  <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full flex items-center gap-1">
    <Lock size={10} />
    PRO
  </span>
);

// =============================================================================
// MAIN APP
// =============================================================================

function App() {
  const [loading, setLoading] = useState(true);
  const [todayStats, setTodayStats] = useState(null);
  const [weekStats, setWeekStats] = useState(null);
  const [periodStats, setPeriodStats] = useState(null);
  const [settings, setSettings] = useState(null);
  const [todayEntry, setTodayEntry] = useState(null);
  const [modal, setModal] = useState(null);
  const [settingsModal, setSettingsModal] = useState(false);
  const [showStatsDashboard, setShowStatsDashboard] = useState(false);
  
  // Team forecast state (Individual+ plans)
  const [teamForecast, setTeamForecast] = useState(null);
  const [topSignals, setTopSignals] = useState([]);
  const [showTeamDashboard, setShowTeamDashboard] = useState(true); // Always show for Individual+
  
  // Form states
  const [bookingProfit, setBookingProfit] = useState('');
  const [isPrepaid, setIsPrepaid] = useState(false);
  const [hasRefundProtection, setHasRefundProtection] = useState(false);
  const [timeSinceLast, setTimeSinceLast] = useState('');
  const [spinAmount, setSpinAmount] = useState('');
  const [isMegaSpin, setIsMegaSpin] = useState(false);
  const [miscAmount, setMiscAmount] = useState('');
  const [miscSource, setMiscSource] = useState('request_lead');
  const [callsInput, setCallsInput] = useState('');
  const [pesoRateInput, setPesoRateInput] = useState('');
  
  // Edit booking state
  const [editingBooking, setEditingBooking] = useState(null);
  
  const today = new Date().toISOString().split('T')[0];
  const isPro = settings?.user_plan && ['pro', 'group'].includes(settings.user_plan);
  const isIndividualOrHigher = settings?.user_plan && ['pro', 'group'].includes(settings.user_plan);
  
  const fetchData = useCallback(async () => {
    try {
      const [todayRes, settingsRes, entryRes] = await Promise.all([
        axios.get(`${API}/stats/today`, { headers: getAuthHeaders() }),
        axios.get(`${API}/settings`, { headers: getAuthHeaders() }),
        axios.get(`${API}/entries/today`, { headers: getAuthHeaders() }),
      ]);
      setTodayStats(todayRes.data);
      setSettings(settingsRes.data);
      setTodayEntry(entryRes.data);
      setCallsInput(String(entryRes.data.calls_received || 0));
      setPesoRateInput(String(settingsRes.data.peso_rate || 17.50));
      
      // Try to fetch pro stats
      try {
        const [weekRes, periodRes] = await Promise.all([
          axios.get(`${API}/stats/week`, { headers: getAuthHeaders() }),
          axios.get(`${API}/stats/period`, { headers: getAuthHeaders() }),
        ]);
        setWeekStats(weekRes.data);
        setPeriodStats(periodRes.data);
      } catch (e) {
        // Stats not available
      }
      
      // Fetch team forecast and signals for Individual+ plans
      if (settingsRes.data?.user_plan && ['individual', 'pro', 'group'].includes(settingsRes.data.user_plan)) {
        try {
          const [forecastRes, signalsRes] = await Promise.all([
            axios.get(`${API}/team/forecast`, { headers: getAuthHeaders() }),
            axios.get(`${API}/team/top-signals`, { headers: getAuthHeaders() }),
          ]);
          setTeamForecast(forecastRes.data);
          setTopSignals(signalsRes.data.signals || []);
        } catch (e) {
          console.error('Error fetching team data:', e);
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Listen for kpi_updated events to refresh data
  useEffect(() => {
    const handleKpiUpdated = () => {
      console.log('kpi_updated event received, refreshing data...');
      fetchData();
    };

    window.addEventListener('kpi_updated', handleKpiUpdated);
    
    return () => {
      window.removeEventListener('kpi_updated', handleKpiUpdated);
    };
  }, [fetchData]);
  
  const updateCalls = async () => {
    try {
      await axios.put(`${API}/entries/${today}/calls?calls_received=${parseInt(callsInput) || 0}`, null, { headers: getAuthHeaders() });
      toast.success('Calls updated!');
      fetchData();
    } catch (error) {
      toast.error('Failed to update calls');
    }
  };
  
  const addBooking = async () => {
    if (!bookingProfit) return;
    
    try {
      await axios.post(`${API}/entries/${today}/bookings`, {
        profit: parseFloat(bookingProfit),
        is_prepaid: isPrepaid,
        has_refund_protection: hasRefundProtection,
        time_since_last: parseInt(timeSinceLast) || 0,
      }, { headers: getAuthHeaders() });
      
      toast.success('Booking added!');
      setBookingProfit('');
      setIsPrepaid(false);
      setHasRefundProtection(false);
      setTimeSinceLast('');
      setModal(null);
      fetchData();
      // Dispatch event for real-time updates
      window.dispatchEvent(new Event('kpi_updated'));
    } catch (error) {
      toast.error('Failed to add booking');
    }
  };
  
  const addSpin = async () => {
    if (!spinAmount) return;
    const prepaidCount = todayStats?.reservations?.prepaid_count || 0;
    try {
      await axios.post(`${API}/entries/${today}/spins`, {
        amount: parseFloat(spinAmount),
        is_mega: isMegaSpin,
        booking_number: prepaidCount,
      }, { headers: getAuthHeaders() });
      toast.success('Spin added!');
      setSpinAmount('');
      setIsMegaSpin(false);
      setModal(null);
      fetchData();
      // Dispatch event for real-time updates
      window.dispatchEvent(new Event('kpi_updated'));
    } catch (error) {
      toast.error('Failed to add spin');
    }
  };
  
  const addMiscIncome = async () => {
    if (!miscAmount) return;
    try {
      await axios.post(`${API}/entries/${today}/misc`, {
        amount: parseFloat(miscAmount),
        source: miscSource,
      }, { headers: getAuthHeaders() });
      toast.success('Misc income added!');
      setMiscAmount('');
      setMiscSource('request_lead');
      setModal(null);
      fetchData();
      // Dispatch event for real-time updates
      window.dispatchEvent(new Event('kpi_updated'));
    } catch (error) {
      toast.error('Failed to add misc income');
    }
  };
  
  const updatePesoRate = async () => {
    try {
      await axios.put(`${API}/settings`, { peso_rate: parseFloat(pesoRateInput) }, { headers: getAuthHeaders() });
      toast.success('Peso rate updated!');
      setSettingsModal(false);
      fetchData();
      // Dispatch event for real-time updates
      window.dispatchEvent(new Event('kpi_updated'));
    } catch (error) {
      toast.error('Failed to update peso rate');
    }
  };
  
  const exportCSV = async () => {
    window.open(`${API}/export/csv`, '_blank');
  };
  
  const deleteBooking = async (bookingId) => {
    if (!window.confirm('Delete this booking?')) return;
    try {
      await axios.delete(`${API}/entries/${today}/bookings/${bookingId}`, { headers: getAuthHeaders() });
      toast.success('Booking deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete booking');
    }
  };

  const startEditBooking = (booking) => {
    setEditingBooking(booking);
    setBookingProfit(String(booking.profit));
    setIsPrepaid(booking.is_prepaid);
    setHasRefundProtection(booking.has_refund_protection);
    setTimeSinceLast(String(booking.time_since_last || ''));
    setModal('edit-booking');
  };

  const updateBooking = async () => {
    if (!bookingProfit || !editingBooking) return;
    try {
      await axios.put(`${API}/entries/${today}/bookings/${editingBooking.id}`, {
        profit: parseFloat(bookingProfit),
        is_prepaid: isPrepaid,
        has_refund_protection: hasRefundProtection,
        time_since_last: parseInt(timeSinceLast) || 0,
      }, { headers: getAuthHeaders() });
      toast.success('Booking updated!');
      setBookingProfit('');
      setIsPrepaid(false);
      setHasRefundProtection(false);
      setTimeSinceLast('');
      setEditingBooking(null);
      setModal(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to update booking');
    }
  };

  
  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="animate-spin text-orange-500" size={40} />
      </div>
    );
  }

  // Show stats dashboard if toggled
  if (showStatsDashboard) {
    return <StatsDashboard onBack={() => setShowStatsDashboard(false)} />;
  }
  
  const stats = todayStats;
  const prepaidCount = stats?.reservations?.prepaid_count || 0;
  const untilNextSpin = 4 - (prepaidCount % 4);
  const spinReady = prepaidCount > 0 && prepaidCount % 4 === 0;
  
  return (
    <div className="min-h-screen bg-black text-white">
      <Toaster position="top-center" theme="dark" />
      
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur border-b border-zinc-800 px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">KPI Tracker</h1>
            <p className="text-xs text-zinc-500">
              ⭐ Pro Plan
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowStatsDashboard(true)}
              className="p-2 hover:bg-zinc-800 rounded-lg"
              data-testid="stats-dashboard-btn"
              title="Live Goals Dashboard"
            >
              <BarChart3 size={20} className="text-zinc-400" />
            </button>
            <button
              onClick={() => setSettingsModal(true)}
              className="p-2 hover:bg-zinc-800 rounded-lg"
              data-testid="settings-btn"
            >
              <Settings size={20} className="text-zinc-400" />
            </button>
            <button
              onClick={fetchData}
              className="p-2 hover:bg-zinc-800 rounded-lg"
              data-testid="refresh-btn"
            >
              <RefreshCw size={20} className="text-zinc-400" />
            </button>
          </div>
        </div>
      </header>
      
      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-4 space-y-4 pb-32">
        
        {/* Team Forecast Dashboard - Individual+ Plans */}
        {isIndividualOrHigher && showTeamDashboard && teamForecast && (
          <ForecastDashboard forecast={teamForecast} signals={topSignals} />
        )}
        
        {/* Dynamic Goals Display */}
        <GoalDisplay userId={settings?.user_id} />
        
        {/* Combined Goal Banner */}
        {stats && (
          <div 
            className={`rounded-xl p-4 ${
              stats.combined.status === 'ahead' 
                ? 'bg-emerald-500/20 border border-emerald-500/50' 
                : 'bg-orange-500/20 border border-orange-500/50'
            }`}
            data-testid="combined-banner"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Combined Goal (Main Target)</p>
                <p className="text-2xl font-bold">
                  ${stats.combined.current.toFixed(2)} / ${stats.combined.goal.toFixed(2)}
                </p>
              </div>
              <Zap size={32} className={stats.combined.status === 'ahead' ? 'text-emerald-400' : 'text-orange-400'} />
            </div>
            <p className={`text-sm mt-1 ${stats.combined.status === 'ahead' ? 'text-emerald-400' : 'text-orange-400'}`}>
              {stats.combined.status === 'ahead' 
                ? `Ahead by $${stats.combined.diff.toFixed(2)}` 
                : `Behind by $${Math.abs(stats.combined.diff).toFixed(2)}`}
            </p>
          </div>
        )}
        
        {/* Current Time Clock */}
        <SimpleClock />
        
        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 gap-3">
            <StatCard
              title="Calls"
              icon={Phone}
              current={stats.calls.current}
              goal={stats.calls.goal}
              diff={stats.calls.diff}
              status={stats.calls.status}
            />
            <StatCard
              title="Reservations"
              icon={Calendar}
              current={stats.reservations.current}
              goal={stats.reservations.goal}
              diff={stats.reservations.diff}
              status={stats.reservations.status}
            />
            <StatCard
              title="Profit"
              icon={DollarSign}
              current={stats.profit.current}
              goal={stats.profit.goal}
              diff={stats.profit.diff}
              status={stats.profit.status}
              isMoney
            />
            <StatCard
              title="Spins"
              icon={Star}
              current={stats.spins.current}
              goal={stats.spins.goal}
              diff={stats.spins.diff}
              status={stats.spins.status}
              isMoney
            />
          </div>
        )}
        
        {/* Conversion & Time */}
        {stats && (
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-zinc-900 rounded-xl p-3 border border-zinc-800">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp size={14} className="text-zinc-500" />
                <span className="text-xs text-zinc-500">Conversion</span>
              </div>
              <span className={`text-xl font-bold ${stats.conversion_rate.status === 'ahead' ? 'text-emerald-400' : 'text-red-400'}`}>
                {stats.conversion_rate.current}%
              </span>
              <span className="text-xs text-zinc-500 ml-2">/ {stats.conversion_rate.goal}%</span>
            </div>
            <div className="bg-zinc-900 rounded-xl p-3 border border-zinc-800">
              <div className="flex items-center gap-2 mb-1">
                <Clock size={14} className="text-zinc-500" />
                <span className="text-xs text-zinc-500">Avg Time</span>
              </div>
              <span className={`text-xl font-bold ${stats.avg_time.status === 'ahead' ? 'text-emerald-400' : 'text-red-400'}`}>
                {stats.avg_time.current} min
              </span>
              <span className="text-xs text-zinc-500 ml-2">/ ≤{stats.avg_time.goal}</span>
            </div>
          </div>
        )}
        
        {/* Calls Input */}
        <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
          <h3 className="text-sm font-semibold text-zinc-400 mb-3">Update Calls</h3>
          <div className="flex gap-2">
            <input
              type="number"
              value={callsInput}
              onChange={(e) => setCallsInput(e.target.value)}
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white"
              placeholder="Calls received"
              data-testid="calls-input"
            />
            <button
              onClick={updateCalls}
              className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg font-semibold"
              data-testid="update-calls-btn"
            >
              Update
            </button>
          </div>
        </div>
        
        {/* Next Spin Card */}
        <div className={`rounded-xl p-4 border ${spinReady ? 'bg-amber-500/20 border-amber-500' : 'bg-zinc-900 border-zinc-800'}`}>
          <div className="flex items-center gap-2 mb-2">
            <Star size={18} className={spinReady ? 'text-amber-400' : 'text-zinc-500'} />
            <span className="text-sm font-semibold text-zinc-400">Next Spin</span>
          </div>
          <p className="text-white">
            {spinReady 
              ? '🎰 Spin earned! Add it now!' 
              : `${untilNextSpin} more PREPAID booking(s) until spin`}
          </p>
          <p className="text-xs text-zinc-500 mt-1">
            Prepaid bookings: {prepaidCount} (Only prepaid count toward spins)
          </p>
        </div>
        
        {/* Action Buttons */}
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => setModal('booking')}
            className="bg-orange-500 hover:bg-orange-600 text-white rounded-xl p-4 flex flex-col items-center gap-2"
            data-testid="add-booking-btn"
          >
            <Calendar size={24} />
            <span className="text-sm font-semibold">Booking</span>
          </button>
          <button
            onClick={() => setModal('spin')}
            className="bg-blue-500 hover:bg-blue-600 text-white rounded-xl p-4 flex flex-col items-center gap-2"
            data-testid="add-spin-btn"
          >
            <Star size={24} />
            <span className="text-sm font-semibold">Spin</span>
          </button>
          <button
            onClick={() => setModal('misc')}
            className="bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl p-4 flex flex-col items-center gap-2"
            data-testid="add-misc-btn"
          >
            <Plus size={24} />
            <span className="text-sm font-semibold">Misc</span>
          </button>
        </div>
        
        {/* Today's Earnings */}
        {stats?.earnings && (
          <EarningsCard
            title="Today's Earnings"
            usd={stats.earnings.usd}
            pesos={stats.earnings.pesos}
            pesoRate={stats.earnings.peso_rate}
          />
        )}
        
        {/* Week & Period Earnings */}
        {weekStats?.earnings && (
          <EarningsCard
            title="This Week's Earnings"
            usd={weekStats.earnings.usd}
            pesos={weekStats.earnings.pesos}
            pesoRate={weekStats.earnings.peso_rate}
          />
        )}
        {periodStats?.earnings && (
          <EarningsCard
            title="This Pay Period's Earnings"
            usd={periodStats.earnings.usd}
            pesos={periodStats.earnings.pesos}
            pesoRate={periodStats.earnings.peso_rate}
          />
        )}
        
        {/* Export Button */}
        <button
          onClick={exportCSV}
          className="w-full bg-zinc-800 hover:bg-zinc-700 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
          data-testid="export-btn"
        >
          <Download size={18} />
          Export to CSV
        </button>
        
        {/* Today's Bookings List */}
        {todayEntry?.bookings?.length > 0 && (
          <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
            <h3 className="text-sm font-semibold text-zinc-400 mb-3">
              Today's Bookings ({todayEntry.bookings.length})
            </h3>
            <div className="space-y-2">
              {[...todayEntry.bookings].reverse().map((booking) => (
                <div key={booking.id} className="flex items-center justify-between bg-zinc-800 rounded-lg p-3">
                  <div>
                    <span className="text-lg font-bold text-emerald-400">
                      ${booking.profit.toFixed(2)}
                    </span>
                    <div className="flex gap-2 mt-1">
                      {booking.is_prepaid && (
                        <span className="text-xs bg-blue-500/30 text-blue-400 px-2 py-0.5 rounded">Prepaid</span>
                      )}
                      {booking.has_refund_protection && (
                        <span className="text-xs bg-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded">Refund</span>
                      )}
                      {booking.time_since_last > 0 && (
                        <span className="text-xs text-zinc-500">{booking.time_since_last} min</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => startEditBooking(booking)}
                      className="p-2 hover:bg-blue-500/20 rounded-lg"
                    >
                      <Settings size={16} className="text-blue-400" />
                    </button>
                    <button
                      onClick={() => deleteBooking(booking.id)}
                      className="p-2 hover:bg-red-500/20 rounded-lg"
                    >
                      <Trash2 size={16} className="text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
      
      {/* Booking Modal */}
      <Modal isOpen={modal === 'booking'} onClose={() => setModal(null)} title="Add Booking">
        <Input
          label="Profit Amount ($)"
          type="number"
          step="0.01"
          placeholder="0.00"
          value={bookingProfit}
          onChange={(e) => setBookingProfit(e.target.value)}
          data-testid="booking-profit-input"
        />
        <Input
          label="Time Since Last Booking (min)"
          type="number"
          placeholder="0"
          value={timeSinceLast}
          onChange={(e) => setTimeSinceLast(e.target.value)}
        />
        <Toggle label="Prepaid (counts toward spin)" checked={isPrepaid} onChange={setIsPrepaid} />
        <Toggle label="Refund Protection" checked={hasRefundProtection} onChange={setHasRefundProtection} />
        <button
          onClick={addBooking}
          className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 rounded-xl font-semibold"
          data-testid="submit-booking-btn"
        >
          Add Booking
        </button>
      </Modal>

      {/* Edit Booking Modal */}
      <Modal isOpen={modal === 'edit-booking'} onClose={() => { setModal(null); setEditingBooking(null); }} title="Edit Booking">
        <Input
          label="Profit Amount ($)"
          type="number"
          step="0.01"
          placeholder="0.00"
          value={bookingProfit}
          onChange={(e) => setBookingProfit(e.target.value)}
        />
        <Input
          label="Time Since Last Booking (min)"
          type="number"
          placeholder="30"
          value={timeSinceLast}
          onChange={(e) => setTimeSinceLast(e.target.value)}
        />
        <Toggle label="Prepaid (counts toward spin)" checked={isPrepaid} onChange={setIsPrepaid} />
        <Toggle label="Refund Protection" checked={hasRefundProtection} onChange={setHasRefundProtection} />
        <button
          onClick={updateBooking}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-xl font-semibold"
        >
          Update Booking
        </button>
      </Modal>
      
      {/* Spin Modal */}
      <Modal isOpen={modal === 'spin'} onClose={() => setModal(null)} title="Add Spin">
        <Input
          label="Spin Amount ($)"
          type="number"
          step="0.01"
          placeholder="0.00"
          value={spinAmount}
          onChange={(e) => setSpinAmount(e.target.value)}
          data-testid="spin-amount-input"
        />
        <Toggle label="Mega Spin (every 4th spin)" checked={isMegaSpin} onChange={setIsMegaSpin} />
        <button
          onClick={addSpin}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-xl font-semibold"
          data-testid="submit-spin-btn"
        >
          Add Spin
        </button>
      </Modal>
      
      {/* Misc Modal */}
      <Modal isOpen={modal === 'misc'} onClose={() => setModal(null)} title="Add Misc Income">
        <Input
          label="Amount ($)"
          type="number"
          step="0.01"
          placeholder="0.00"
          value={miscAmount}
          onChange={(e) => setMiscAmount(e.target.value)}
          data-testid="misc-amount-input"
        />
        <div className="mb-4">
          <label className="block text-sm text-zinc-400 mb-2">Source</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setMiscSource('request_lead')}
              className={`py-2 rounded-lg font-medium ${
                miscSource === 'request_lead' ? 'bg-emerald-500 text-white' : 'bg-zinc-800 text-zinc-400'
              }`}
            >
              Request Lead
            </button>
            <button
              type="button"
              onClick={() => setMiscSource('refund_protection')}
              className={`py-2 rounded-lg font-medium ${
                miscSource === 'refund_protection' ? 'bg-emerald-500 text-white' : 'bg-zinc-800 text-zinc-400'
              }`}
            >
              Refund Protection
            </button>
          </div>
        </div>
        <button
          onClick={addMiscIncome}
          className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-3 rounded-xl font-semibold"
          data-testid="submit-misc-btn"
        >
          Add Income
        </button>
      </Modal>
      
      {/* Settings Modal */}
      <Modal isOpen={settingsModal} onClose={() => setSettingsModal(false)} title="Settings">
        <SettingsPanel 
          goals={settings?.goals || {}} 
          setGoals={(newGoals) => {
            setSettings(prev => ({ ...prev, goals: newGoals }));
          }}
          onSettingsChange={(data) => {
            setSettings(prev => ({
              ...prev,
              peso_rate: data?.conversion?.exchange_rate || prev?.peso_rate
            }));
          }}
        />
      </Modal>
    </div>
  );
}

export default App;

