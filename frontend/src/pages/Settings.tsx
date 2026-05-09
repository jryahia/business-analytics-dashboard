import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Cloud,
  RefreshCw,
  Trash2,
  LogOut,
  Download,
  Save,
  Zap,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/api';

export default function Settings() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || 'http://localhost:8000');
  const [refreshInterval, setRefreshInterval] = useState('60');
  const [statusMsg, setStatusMsg] = useState<{ type: 'ok' | 'error' | 'info'; text: string } | null>(null);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const showStatus = (type: 'ok' | 'error' | 'info', text: string) => {
    setStatusMsg({ type, text });
    setTimeout(() => setStatusMsg(null), 4000);
  };

  const handleSave = () => {
    localStorage.setItem('api_url', apiUrl);
    localStorage.setItem('refresh_interval', refreshInterval);
    showStatus('ok', 'Settings saved');
  };

  const handleTestApi = async () => {
    try {
      const res = await api.get('/health');
      showStatus('ok', `Connected! Server: ${JSON.stringify(res)}`);
    } catch (err: any) {
      showStatus('error', `Connection failed: ${err.message}`);
    }
  };

  const handleClearCache = () => {
    localStorage.removeItem('dashboard_cache');
    showStatus('info', 'Cache cleared');
  };

  const handleExportAll = async () => {
    try {
      const blob = await api.get('/api/export/all', { responseType: 'blob' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'analytics_export.zip';
      a.click();
      URL.revokeObjectURL(url);
      showStatus('ok', 'Export downloaded');
    } catch (err: any) {
      showStatus('error', `Export failed: ${err.message}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const SectionCard = ({ children }: { children: React.ReactNode }) => (
    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6 space-y-4">{children}</div>
  );

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <User className="w-6 h-6 text-gray-400" />
          Settings
        </h1>
        <p className="text-sm text-gray-500 mt-1">Manage your account, connections, and preferences</p>
      </div>

      {/* Profile */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Profile</h2>
        <SectionCard>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-700 flex items-center justify-center text-lg font-bold text-white">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div>
              <p className="text-white font-medium">{user?.email || 'User'}</p>
              <p className="text-xs text-gray-500">Role: {user?.role || 'Admin'}</p>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Connection */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Connection</h2>
        <SectionCard>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Backend API URL</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Cloud className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                  <input
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Auto-refresh Interval</label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              >
                <option value="0">Off</option>
                <option value="30">30 seconds</option>
                <option value="60">1 minute</option>
                <option value="300">5 minutes</option>
              </select>
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-700 text-sm text-white hover:bg-blue-600 transition-colors">
                <Save className="w-4 h-4" /> Save Settings
              </button>
              <button onClick={handleTestApi} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-700 text-sm text-gray-300 hover:bg-gray-800 transition-colors">
                <Zap className="w-4 h-4" /> Test Connection
              </button>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Data Management */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Data Management</h2>
        <SectionCard>
          <p className="text-sm text-gray-400">Clear cached data or export all dashboards and datasets.</p>
          <div className="flex gap-3">
            <button onClick={handleClearCache} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-700 text-sm text-amber-400 hover:bg-gray-800 transition-colors">
              <Trash2 className="w-4 h-4" /> Clear Cache
            </button>
            <button onClick={handleExportAll} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-700 text-sm text-green-400 hover:bg-gray-800 transition-colors">
              <Download className="w-4 h-4" /> Export All
            </button>
          </div>
        </SectionCard>
      </div>

      {/* Danger Zone */}
      <div>
        <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">Danger Zone</h2>
        <SectionCard>
          <p className="text-sm text-red-400/80">Irreversible actions. Proceed with caution.</p>
          {!showLogoutConfirm ? (
            <button
              onClick={() => setShowLogoutConfirm(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-800/50 text-sm text-red-300 hover:bg-red-800 transition-colors border border-red-700/50"
            >
              <LogOut className="w-4 h-4" /> Logout
            </button>
          ) : (
            <div className="flex items-center gap-3 p-3 bg-red-900/30 border border-red-700/50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <span className="text-sm text-red-300">Are you sure you want to logout?</span>
              <button onClick={handleLogout} className="ml-auto px-3 py-1.5 rounded bg-red-700 text-sm text-white hover:bg-red-600">Yes, Logout</button>
              <button onClick={() => setShowLogoutConfirm(false)} className="px-3 py-1.5 rounded border border-gray-700 text-sm text-gray-400 hover:bg-gray-800">Cancel</button>
            </div>
          )}
        </SectionCard>
      </div>

      {/* Status Messages */}
      {statusMsg && (
        <div className={`fixed bottom-6 right-6 px-5 py-3 rounded-lg shadow-lg text-sm flex items-center gap-2 border ${
          statusMsg.type === 'ok' ? 'bg-green-900/90 text-green-300 border-green-700' :
          statusMsg.type === 'error' ? 'bg-red-900/90 text-red-300 border-red-700' :
          'bg-blue-900/90 text-blue-300 border-blue-700'
        }`}>
          {statusMsg.type === 'ok' ? <CheckCircle2 className="w-4 h-4" /> :
           statusMsg.type === 'error' ? <AlertTriangle className="w-4 h-4" /> :
           <RefreshCw className="w-4 h-4" />}
          {statusMsg.text}
        </div>
      )}

      {/* About */}
      <div className="pt-4 border-t border-gray-800">
        <p className="text-xs text-gray-600">
          Business Analytics Dashboard v1.0.0 &middot; Built with React + FastAPI + Flet
        </p>
      </div>
    </div>
  );
}
