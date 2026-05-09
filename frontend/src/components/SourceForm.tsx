import React, { useState } from 'react';
import { Plug, Zap, Loader2 } from 'lucide-react';
import { api } from '../lib/api';

interface SourceFormProps {
  onSubmit?: (source: any) => void;
}

export default function SourceForm({ onSubmit }: SourceFormProps) {
  const [name, setName] = useState('');
  const [dbType, setDbType] = useState('postgresql');
  const [host, setHost] = useState('');
  const [port, setPort] = useState('5432');
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const dbTypes = [
    { value: 'postgresql', label: 'PostgreSQL', defaultPort: '5432' },
    { value: 'mysql', label: 'MySQL', defaultPort: '3306' },
    { value: 'sqlite', label: 'SQLite', defaultPort: '' },
    { value: 'mssql', label: 'SQL Server', defaultPort: '1433' },
  ];

  const handleDbTypeChange = (val: string) => {
    setDbType(val);
    const t = dbTypes.find((d) => d.value === val);
    if (t?.defaultPort) setPort(t.defaultPort);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);
    try {
      const res = await api.post('/api/datasources/test', {
        name, db_type: dbType, host, port: parseInt(port) || 5432,
        database, username, password,
      });
      setTestResult({ ok: res.success ?? true, msg: res.success ? 'Connection successful!' : (res.error || 'Failed') });
    } catch (err: any) {
      setTestResult({ ok: false, msg: err?.response?.data?.detail || err.message || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await api.post('/api/datasources', {
        name, db_type: dbType, host, port: parseInt(port) || 5432,
        database, username, password,
      });
      onSubmit?.(res);
      setName(''); setHost(''); setPort('5432'); setDatabase(''); setUsername(''); setPassword('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="flex items-center gap-2 mb-1">
        <Plug className="w-4 h-4 text-blue-400" />
        <span className="text-sm font-medium text-gray-300">New Data Source</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1.5">Source Name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Production DB"
            required
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1.5">Database Type</label>
          <select
            value={dbType}
            onChange={(e) => handleDbTypeChange(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {dbTypes.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label className="block text-xs text-gray-500 mb-1.5">Host</label>
            <input
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="localhost"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="w-20">
            <label className="block text-xs text-gray-500 mb-1.5">Port</label>
            <input
              value={port}
              onChange={(e) => setPort(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1.5">Database</label>
          <input
            value={database}
            onChange={(e) => setDatabase(e.target.value)}
            placeholder="mydb"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1.5">Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1.5">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {testResult && (
        <div className={`px-4 py-2.5 rounded-lg text-sm flex items-center gap-2 ${
          testResult.ok ? 'bg-green-500/10 text-green-400 border border-green-500/30' : 'bg-red-500/10 text-red-400 border border-red-500/30'
        }`}>
          <Zap className="w-4 h-4" />
          {testResult.msg}
        </div>
      )}

      {error && (
        <div className="px-4 py-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleTest}
          disabled={testing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-700 text-sm text-gray-300 hover:bg-gray-800 disabled:opacity-50 transition-colors"
        >
          {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          Test Connection
        </button>
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-700 text-sm text-white hover:bg-blue-600 disabled:opacity-50 transition-colors"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Save Source
        </button>
      </div>
    </form>
  );
}
