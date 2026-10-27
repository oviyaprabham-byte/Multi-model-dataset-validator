import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory, deleteHistory, clearAllHistory, getResult } from '../services/api';
import { useValidation } from '../context/ValidationContext';
import toast from 'react-hot-toast';
import {
  History as HistoryIcon, Trash2, Search, CheckCircle2,
  XCircle, RefreshCw, UploadCloud, Eye, AlertTriangle, Trash
} from 'lucide-react';

const badgeClass = {
  Excellent: { cls: 'badge-excellent', emoji: '🏆' },
  Good: { cls: 'badge-good', emoji: '✅' },
  Average: { cls: 'badge-average', emoji: '⚠️' },
  Poor: { cls: 'badge-poor', emoji: '❌' },
};

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [restoringId, setRestoringId] = useState(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const { setResult } = useValidation();
  const navigate = useNavigate();

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getHistory();
      setHistory(data);
    } catch {
      toast.error('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleDelete = async (sessionId, filename) => {
    try {
      await deleteHistory(sessionId);
      setHistory(prev => prev.filter(h => h.session_id !== sessionId));
      toast.success(`Deleted: ${filename}`);
    } catch {
      toast.error('Failed to delete entry');
    }
  };

  const handleRestore = async (entry) => {
    setRestoringId(entry.session_id);
    try {
      const result = await getResult(entry.session_id);
      setResult(result);
      toast.success('Results restored!');
      navigate('/results');
    } catch (err) {
      const msg = err.response?.status === 404
        ? 'This session is no longer in memory. Restart the backend and re-validate to restore results.'
        : 'Failed to restore results';
      toast.error(msg, { duration: 5000 });
    } finally {
      setRestoringId(null);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllHistory();
      setHistory([]);
      setConfirmClear(false);
      toast.success('All history cleared');
    } catch {
      toast.error('Failed to clear history');
    }
  };

  const filtered = history.filter(h =>
    h.filename?.toLowerCase().includes(search.toLowerCase()) ||
    h.dataset_type?.toLowerCase().includes(search.toLowerCase()) ||
    h.badge?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Validation History</h1>
          <p className="page-subtitle">Track and restore your previous dataset validations</p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="btn btn-outline btn-sm" onClick={fetchHistory}>
            <RefreshCw size={14} /> Refresh
          </button>
          {history.length > 0 && (
            <button
              className="btn btn-outline btn-sm"
              style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.3)' }}
              onClick={() => setConfirmClear(true)}
            >
              <Trash size={14} /> Clear All
            </button>
          )}
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/')}>
            <UploadCloud size={14} /> New Upload
          </button>
        </div>
      </div>

      <div className="page-body">

        {/* Confirm Clear Modal */}
        {confirmClear && (
          <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            backdropFilter: 'blur(4px)', zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div className="card" style={{ maxWidth: 400, width: '90%', textAlign: 'center' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
              <h3 style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 18, marginBottom: 8 }}>
                Clear All History?
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 24 }}>
                This will permanently delete all {history.length} validation records. This action cannot be undone.
              </p>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <button className="btn btn-outline" onClick={() => setConfirmClear(false)}>
                  Cancel
                </button>
                <button className="btn btn-danger" onClick={handleClearAll}>
                  <Trash size={14} /> Clear All
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="card animate-fade-in" style={{ padding: '14px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Search size={18} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search by filename, type, or rating…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                flex: 1, background: 'none', border: 'none', outline: 'none',
                color: 'var(--text-primary)', fontSize: 14,
              }}
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Info banner */}
        <div style={{
          background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 10, padding: '10px 16px',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <AlertTriangle size={14} color="var(--accent-light)" />
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            <strong style={{ color: 'var(--accent-light)' }}>Restore Results</strong> — clicking the eye icon restores a session's full results into the app.
            Sessions are only available while the backend server is running.
          </span>
        </div>

        {/* History Table */}
        <div className="card animate-fade-in-delay-1">
          <div className="section-header">
            <div className="section-dot" />
            <span className="section-title">Recent Validations</span>
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
              {filtered.length} record{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div className="loading-spinner" style={{ margin: '0 auto' }} />
              <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 12 }}>Loading history…</div>
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <HistoryIcon size={48} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
              <div style={{ color: 'var(--text-secondary)', fontSize: 16, fontWeight: 600 }}>
                {search ? 'No results found' : 'No validation history yet'}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
                {search ? 'Try a different search term' : 'Upload a dataset to get started'}
              </div>
              {!search && (
                <button
                  className="btn btn-primary"
                  style={{ marginTop: 20 }}
                  onClick={() => navigate('/')}
                >
                  <UploadCloud size={16} /> Upload Dataset
                </button>
              )}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Type</th>
                    <th>Score</th>
                    <th>Rating</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((entry) => {
                    const badge = badgeClass[entry.badge] || { cls: 'badge-accent', emoji: '📊' };
                    const isRestoring = restoringId === entry.session_id;
                    return (
                      <tr key={entry.session_id}>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {entry.filename}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, fontFamily: 'JetBrains Mono, monospace' }}>
                            {entry.session_id.slice(0, 8)}…
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-accent" style={{ textTransform: 'uppercase' }}>
                            {entry.dataset_type}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{
                              width: 60, height: 6, background: 'rgba(99,102,241,0.1)',
                              borderRadius: 3, overflow: 'hidden'
                            }}>
                              <div style={{
                                height: '100%',
                                width: `${entry.quality_score}%`,
                                background: entry.quality_score >= 80 ? 'var(--success)' : entry.quality_score >= 60 ? 'var(--warning)' : 'var(--danger)',
                                borderRadius: 3,
                              }} />
                            </div>
                            <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 13 }}>
                              {entry.quality_score}
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${badge.cls}`}>
                            {badge.emoji} {entry.badge}
                          </span>
                        </td>
                        <td>
                          {entry.is_ready ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <CheckCircle2 size={14} color="var(--success)" />
                              <span style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600 }}>Ready</span>
                            </div>
                          ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <XCircle size={14} color="var(--danger)" />
                              <span style={{ fontSize: 12, color: 'var(--danger)', fontWeight: 600 }}>Not Ready</span>
                            </div>
                          )}
                        </td>
                        <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                          {entry.timestamp}
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button
                              className="btn btn-outline btn-sm"
                              style={{ color: 'var(--accent-light)', borderColor: 'rgba(99,102,241,0.3)' }}
                              onClick={() => handleRestore(entry)}
                              disabled={isRestoring}
                              title="Restore results for this session"
                            >
                              {isRestoring ? (
                                <div className="loading-spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                              ) : (
                                <Eye size={12} />
                              )}
                            </button>
                            <button
                              className="btn btn-outline btn-sm"
                              style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)' }}
                              onClick={() => handleDelete(entry.session_id, entry.filename)}
                              title="Delete this record"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Stats Summary */}
        {history.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }} className="animate-fade-in-delay-2">
            {[
              { label: 'Total Validations', value: history.length, icon: '📊', color: '#6366F1' },
              { label: 'Ready Datasets', value: history.filter(h => h.is_ready).length, icon: '✅', color: '#10B981' },
              { label: 'Not Ready', value: history.filter(h => !h.is_ready).length, icon: '❌', color: '#EF4444' },
              {
                label: 'Avg Score',
                value: `${(history.reduce((a, h) => a + h.quality_score, 0) / history.length).toFixed(1)}`,
                icon: '🏆',
                color: '#F59E0B',
              },
            ].map((s) => (
              <div key={s.label} className="stat-card" style={{ background: `${s.color}10`, border: `1px solid ${s.color}20` }}>
                <div className="stat-icon" style={{ background: `${s.color}20`, fontSize: 20 }}>{s.icon}</div>
                <div>
                  <div className="stat-value" style={{ color: s.color, fontSize: 24 }}>{s.value}</div>
                  <div className="stat-label" style={{ fontSize: 11 }}>{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
