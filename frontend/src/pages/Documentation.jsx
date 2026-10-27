import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getDocs, deleteDoc, generateDoc
} from '../services/api';
import toast from 'react-hot-toast';
import {
  FileText, Trash2, Search, RefreshCw, UploadCloud,
  CheckCircle2, XCircle, Bot, AlertTriangle, Trash, Sparkles
} from 'lucide-react';
import DocAgentPanel from '../components/DocAgentPanel';

const badgeClass = {
  Excellent: { cls: 'badge-excellent', emoji: '🏆' },
  Good:      { cls: 'badge-good',      emoji: '✅' },
  Average:   { cls: 'badge-average',   emoji: '⚠️' },
  Poor:      { cls: 'badge-poor',      emoji: '❌' },
};

export default function DocumentationPage() {
  const [docs, setDocs]               = useState([]);
  const [loading, setLoading]         = useState(true);
  const [search, setSearch]           = useState('');
  const [generatingId, setGeneratingId] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null); // { session_id, name }
  const [agentDoc, setAgentDoc]       = useState(null);    // { session_id, dataset_name }
  const navigate = useNavigate();

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const data = await getDocs();
      setDocs(data);
    } catch {
      toast.error('Failed to load documentation list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await deleteDoc(confirmDelete.session_id);
      setDocs(prev => prev.filter(d => d.session_id !== confirmDelete.session_id));
      toast.success(`Deleted: ${confirmDelete.name}`);
    } catch {
      toast.error('Failed to delete documentation');
    } finally {
      setConfirmDelete(null);
    }
  };

  const handleGenerate = async (sessionId, name) => {
    setGeneratingId(sessionId);
    try {
      await generateDoc(sessionId);
      await fetchDocs();
      toast.success(`Documentation regenerated for ${name}`);
    } catch (err) {
      const msg = err.response?.status === 404
        ? 'Session expired — re-validate the dataset to regenerate docs.'
        : 'Failed to regenerate documentation';
      toast.error(msg, { duration: 5000 });
    } finally {
      setGeneratingId(null);
    }
  };

  const filtered = docs.filter(d =>
    d.dataset_name?.toLowerCase().includes(search.toLowerCase()) ||
    d.dataset_type?.toLowerCase().includes(search.toLowerCase()) ||
    d.quality_badge?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dataset Documentation</h1>
          <p className="page-subtitle">AI-generated docs with voice reading and Q&amp;A for each validated dataset</p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="btn btn-outline btn-sm" onClick={fetchDocs}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/')}>
            <UploadCloud size={14} /> New Upload
          </button>
        </div>
      </div>

      <div className="page-body">

        {/* Delete Confirm Modal */}
        {confirmDelete && (
          <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            backdropFilter: 'blur(4px)', zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div className="card" style={{ maxWidth: 400, width: '90%', textAlign: 'center' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🗑️</div>
              <h3 style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 18, marginBottom: 8 }}>
                Delete Documentation?
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 24 }}>
                This will permanently remove the documentation for <strong>{confirmDelete.name}</strong>.
              </p>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <button className="btn btn-outline" onClick={() => setConfirmDelete(null)}>
                  Cancel
                </button>
                <button className="btn btn-danger" onClick={handleDelete}>
                  <Trash size={14} /> Delete
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
            <strong style={{ color: 'var(--accent-light)' }}>Auto-generated</strong> — documentation is created automatically after every validation.
            Click <strong style={{ color: 'var(--accent-light)' }}>🤖 AI Agent</strong> on any row to listen to the doc read aloud and ask questions about the dataset.
          </span>
        </div>

        {/* Documentation Table */}
        <div className="card animate-fade-in-delay-1">
          <div className="section-header">
            <div className="section-dot" />
            <span className="section-title">Generated Documentation</span>
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
              {filtered.length} document{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div className="loading-spinner" style={{ margin: '0 auto' }} />
              <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 12 }}>Loading documentation…</div>
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <FileText size={48} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
              <div style={{ color: 'var(--text-secondary)', fontSize: 16, fontWeight: 600 }}>
                {search ? 'No results found' : 'No documentation yet'}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
                {search ? 'Try a different search term' : 'Upload and validate a dataset to auto-generate documentation'}
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
                    <th>Dataset</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Score</th>
                    <th>Rating</th>
                    <th>AI Ready</th>
                    <th>Generated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((doc) => {
                    const badge = badgeClass[doc.quality_badge] || { cls: 'badge-accent', emoji: '📊' };
                    const isGenerating = generatingId === doc.session_id;
                    return (
                      <tr key={doc.session_id}>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {doc.dataset_name}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, fontFamily: 'JetBrains Mono, monospace' }}>
                            {doc.session_id.slice(0, 8)}…
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-accent" style={{ textTransform: 'uppercase' }}>
                            {doc.dataset_type}
                          </span>
                        </td>
                        <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                          {doc.dataset_size || '—'}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{
                              width: 60, height: 6, background: 'rgba(99,102,241,0.1)',
                              borderRadius: 3, overflow: 'hidden'
                            }}>
                              <div style={{
                                height: '100%',
                                width: `${doc.quality_score ?? 0}%`,
                                background: doc.quality_score >= 80 ? 'var(--success)' : doc.quality_score >= 60 ? 'var(--warning)' : 'var(--danger)',
                                borderRadius: 3,
                              }} />
                            </div>
                            <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 13 }}>
                              {doc.quality_score ?? '—'}
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${badge.cls}`}>
                            {badge.emoji} {doc.quality_badge}
                          </span>
                        </td>
                        <td>
                          {doc.ai_readiness === true ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <CheckCircle2 size={14} color="var(--success)" />
                              <span style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600 }}>Ready</span>
                            </div>
                          ) : doc.ai_readiness === false ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <XCircle size={14} color="var(--danger)" />
                              <span style={{ fontSize: 12, color: 'var(--danger)', fontWeight: 600 }}>Not Ready</span>
                            </div>
                          ) : (
                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>—</span>
                          )}
                        </td>
                        <td style={{ color: 'var(--text-muted)', fontSize: 12, whiteSpace: 'nowrap' }}>
                          {doc.generated_at
                            ? new Date(doc.generated_at).toLocaleString()
                            : '—'
                          }
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'nowrap' }}>
                            {/* AI Agent button */}
                            <button
                              className="btn btn-outline btn-sm"
                              style={{ color: '#a78bfa', borderColor: 'rgba(167,139,250,0.3)', gap: 4 }}
                              onClick={() => setAgentDoc({ session_id: doc.session_id, dataset_name: doc.dataset_name })}
                              title="Open AI Agent — voice reading + Q&A"
                            >
                              <Bot size={12} /> AI Agent
                            </button>
                            {/* Regenerate button */}
                            <button
                              className="btn btn-outline btn-sm"
                              style={{ color: 'var(--accent-light)', borderColor: 'rgba(99,102,241,0.3)' }}
                              onClick={() => handleGenerate(doc.session_id, doc.dataset_name)}
                              disabled={isGenerating}
                              title="Regenerate documentation (requires active session)"
                            >
                              {isGenerating ? (
                                <div className="loading-spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                              ) : (
                                <Sparkles size={12} />
                              )}
                            </button>
                            {/* Delete button */}
                            <button
                              className="btn btn-outline btn-sm"
                              style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)' }}
                              onClick={() => setConfirmDelete({ session_id: doc.session_id, name: doc.dataset_name })}
                              title="Delete documentation"
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
        {docs.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }} className="animate-fade-in-delay-2">
            {[
              { label: 'Total Documents', value: docs.length, icon: '📄', color: '#6366F1' },
              { label: 'AI Ready',        value: docs.filter(d => d.ai_readiness).length, icon: '✅', color: '#10B981' },
              { label: 'Not Ready',       value: docs.filter(d => d.ai_readiness === false).length, icon: '❌', color: '#EF4444' },
              {
                label: 'Avg Score',
                value: docs.length
                  ? `${(docs.reduce((a, d) => a + (d.quality_score || 0), 0) / docs.length).toFixed(1)}`
                  : '—',
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

      {/* AI Agent Panel (drawer) */}
      {agentDoc && (
        <DocAgentPanel
          sessionId={agentDoc.session_id}
          datasetName={agentDoc.dataset_name}
          onClose={() => setAgentDoc(null)}
        />
      )}
    </div>
  );
}
