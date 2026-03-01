import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { ArrowLeft, Loader2 } from 'lucide-react';
import DashboardLayout from './components/DashboardLayout';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;

function StatsDashboard({ onBack }) {
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await axios.get(`${API}/settings`);
        setUserId(res.data.user_id);
      } catch (error) {
        console.error('Error fetching settings:', error);
        toast.error('Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="animate-spin text-orange-500" size={40} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Toaster position="top-center" theme="dark" />

      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur border-b border-zinc-800 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
            data-testid="back-btn"
          >
            <ArrowLeft size={20} className="text-zinc-400" />
          </button>
          <div>
            <h1 className="text-xl font-bold">Live Goals Dashboard</h1>
            <p className="text-xs text-zinc-500">Real-time stats and daily goals</p>
          </div>
        </div>
      </header>

      {/* Dashboard Content */}
      <main className="max-w-4xl mx-auto px-4 py-4 pb-32">
        {userId && <DashboardLayout userId={userId} />}
      </main>
    </div>
  );
}

export default StatsDashboard;
