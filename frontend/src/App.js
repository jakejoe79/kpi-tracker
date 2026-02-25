import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import {
  Phone, Calendar, DollarSign, Star, Clock, TrendingUp,
  Plus, Trash2, Play, Square, Download, Settings, X, Loader2,
  RefreshCw, ChevronDown, ChevronUp, Zap, Lock
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;

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

const WorkTimer = ({ timerStart, onStart, onStop, lastBookingTime, onTimeCalculated }) => {
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  
  useEffect(() => {
    if (timerStart) {
      setIsRunning(true);
      const start = new Date(timerStart).getTime();
      const interval = setInterval(() => {
        const now = Date.now();
        setElapsed(Math.floor((now - start) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setIsRunning(false);
      setElapsed(0);
    }
  }, [timerStart]);
  
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  const handleStart = async () => {
    await onStart();
  };
  
  const handleStop = async () => {
    await onStop();
  };
  
  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock size={18} className="text-zinc-500" />
          <span className="text-sm font-semibold text-zinc-400">Work Timer</span>
        </div>
        {isRunning && (
          <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded-full animate-pulse">
            RUNNING
          </span>
        )}
      </div>
      <div className="text-4xl font-mono font-bold text-white text-center my-4">
        {formatTime(elapsed)}
      </div>
      <div className="flex gap-2">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
            data-testid="start-timer-btn"
          >
            <Play size={18} />
            Start Work
          </button>
        ) : (
          <button
            onClick={handleStop}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
            data-testid="stop-timer-btn"
          >
            <Square size={18} />
            Stop
          </button>
        )}
      </div>
      {isRunning && (
        <p className="text-xs text-zinc-500 text-center mt-2">
          Time will auto-fill when you add a booking
        </p>
      )}
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
  
  const today = new Date().toISOString().split('T')[0];
  const isPro = settings?.user_plan === 'pro';
  
  const fetchData = useCallback(async () => {
    try {
      const [todayRes, settingsRes, entryRes] = await Promise.all([
        axios.get(`${API}/stats/today`),
        axios.get(`${API}/settings`),
        axios.get(`${API}/entries/today`),
      ]);
      setTodayStats(todayRes.data);
      setSettings(settingsRes.data);
      setTodayEntry(entryRes.data);
      setCallsInput(String(entryRes.data.calls_received || 0));
      setPesoRateInput(String(settingsRes.data.peso_rate || 17.50));
      
      // Try to fetch pro stats (will 403 if free)
      try {
        const [weekRes, periodRes] = await Promise.all([
          axios.get(`${API}/stats/week`),
          axios.get(`${API}/stats/period`),
        ]);
        setWeekStats(weekRes.data);
        setPeriodStats(periodRes.data);
      } catch (e) {
        // Free tier - no access
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
  
  const updateCalls = async () => {
    try {
      await axios.put(`${API}/entries/${today}/calls?calls_received=${parseInt(callsInput) || 0}`);
      toast.success('Calls updated!');
      fetchData();
    } catch (error) {
      toast.error('Failed to update calls');
    }
  };
  
  const startTimer = async () => {
    try {
      await axios.post(`${API}/entries/${today}/timer/start`);
      fetchData();
    } catch (error) {
      toast.error('Failed to start timer');
    }
  };
  
  const stopTimer = async () => {
    try {
      await axios.post(`${API}/entries/${today}/timer/stop`);
      fetchData();
    } catch (error) {
      toast.error('Failed to stop timer');
    }
  };
  
  const addBooking = async () => {
    if (!bookingProfit) return;
    
    // Auto-calculate time if timer is running
    let timeValue = parseInt(timeSinceLast) || 0;
    if (todayEntry?.work_timer_start && !timeSinceLast) {
      const start = new Date(todayEntry.work_timer_start).getTime();
      const now = Date.now();
      timeValue = Math.floor((now - start) / 60000); // Convert to minutes
    }
    
    try {
      await axios.post(`${API}/entries/${today}/bookings`, {
        profit: parseFloat(bookingProfit),
        is_prepaid: isPrepaid,
        has_refund_protection: hasRefundProtection,
        time_since_last: timeValue,
      });
      
      // Restart timer for next booking
      if (todayEntry?.work_timer_start) {
        await axios.post(`${API}/entries/${today}/timer/start`);
      }
      
      toast.success('Booking added!');
      setBookingProfit('');
      setIsPrepaid(false);
      setHasRefundProtection(false);
      setTimeSinceLast('');
      setModal(null);
      fetchData();
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
      });
      toast.success('Spin added!');
      setSpinAmount('');
      setIsMegaSpin(false);
      setModal(null);
      fetchData();
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
      });
      toast.success('Misc income added!');
      setMiscAmount('');
      setMiscSource('request_lead');
      setModal(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to add misc income');
    }
  };
  
  const updatePesoRate = async () => {
    try {
      await axios.put(`${API}/settings`, { peso_rate: parseFloat(pesoRateInput) });
      toast.success('Peso rate updated!');
      setSettingsModal(false);
      fetchData();
    } catch (error) {
      toast.error('Failed to update peso rate');
    }
  };
  
  const togglePlan = async () => {
    const newPlan = isPro ? 'free' : 'pro';
    try {
      await axios.put(`${API}/settings`, { user_plan: newPlan });
      toast.success(`Switched to ${newPlan.toUpperCase()} plan`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update plan');
    }
  };
  
  const exportCSV = async () => {
    if (!isPro) {
      toast.error('Upgrade to Pro for data export');
      return;
    }
    window.open(`${API}/export/csv`, '_blank');
  };
  
  const deleteBooking = async (bookingId) => {
    if (!window.confirm('Delete this booking?')) return;
    try {
      await axios.delete(`${API}/entries/${today}/bookings/${bookingId}`);
      toast.success('Booking deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete booking');
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="animate-spin text-orange-500" size={40} />
      </div>
    );
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
              {isPro ? '⭐ Pro Plan' : 'Free Plan'}
            </p>
          </div>
          <div className="flex items-center gap-2">
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
        
        {/* Work Timer */}
        <WorkTimer
          timerStart={todayEntry?.work_timer_start}
          onStart={startTimer}
          onStop={stopTimer}
        />
        
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
        
        {/* Week & Period Earnings (Pro Only) */}
        {isPro ? (
          <>
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
          </>
        ) : (
          <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Lock size={18} className="text-amber-400" />
              <span className="text-amber-400 font-semibold">Pro Features</span>
            </div>
            <p className="text-sm text-zinc-500 mb-3">
              Unlock weekly stats, period stats, history, and CSV export
            </p>
            <button
              onClick={togglePlan}
              className="bg-amber-500 hover:bg-amber-600 text-black font-bold py-2 px-6 rounded-lg"
            >
              Upgrade to Pro
            </button>
          </div>
        )}
        
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
                  <button
                    onClick={() => deleteBooking(booking.id)}
                    className="p-2 hover:bg-red-500/20 rounded-lg"
                  >
                    <Trash2 size={16} className="text-red-500" />
                  </button>
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
          placeholder={todayEntry?.work_timer_start ? 'Auto from timer' : '30'}
          value={timeSinceLast}
          onChange={(e) => setTimeSinceLast(e.target.value)}
        />
        {todayEntry?.work_timer_start && !timeSinceLast && (
          <p className="text-xs text-emerald-400 -mt-2 mb-4">
            ✓ Will auto-fill from running timer
          </p>
        )}
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
        <Input
          label="Peso Conversion Rate (MXN per USD)"
          type="number"
          step="0.01"
          placeholder="17.50"
          value={pesoRateInput}
          onChange={(e) => setPesoRateInput(e.target.value)}
        />
        <button
          onClick={updatePesoRate}
          className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 rounded-xl font-semibold mb-4"
        >
          Save Peso Rate
        </button>
        
        <div className="border-t border-zinc-800 pt-4">
          <h4 className="text-sm font-semibold text-zinc-400 mb-3">Plan</h4>
          <div className="flex items-center justify-between bg-zinc-800 rounded-lg p-3">
            <div>
              <p className="font-semibold">{isPro ? 'Pro Plan' : 'Free Plan'}</p>
              <p className="text-xs text-zinc-500">
                {isPro ? 'Full access to all features' : 'Basic daily tracking only'}
              </p>
            </div>
            <button
              onClick={togglePlan}
              className={`px-4 py-2 rounded-lg font-semibold ${
                isPro ? 'bg-zinc-700 text-zinc-300' : 'bg-amber-500 text-black'
              }`}
            >
              {isPro ? 'Downgrade' : 'Upgrade'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default App;
