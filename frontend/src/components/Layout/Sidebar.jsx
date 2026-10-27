import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  UploadCloud, CheckCircle2, BarChart3, History,
  Zap, Home, ChevronRight, Lock, FileText
} from 'lucide-react';
import { useValidation } from '../../context/ValidationContext';

const navItems = [
  { to: '/', icon: Home, label: 'Upload & Validate', requiresResult: false },
  { to: '/results', icon: CheckCircle2, label: 'Results', requiresResult: true },
  { to: '/dashboard', icon: BarChart3, label: 'Dashboard', requiresResult: true },
  { to: '/history', icon: History, label: 'History', requiresResult: false },
  { to: '/documentation', icon: FileText, label: 'Documentation', requiresResult: false },
];

export default function Sidebar() {
  const location = useLocation();
  const { result, loading } = useValidation();

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Zap size={20} color="white" />
        </div>
        <div>
          <div className="sidebar-logo-text">DataValidator</div>
          <div className="sidebar-logo-sub">ML Dataset Quality Suite</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Navigation</div>
        {navItems.map(({ to, icon: Icon, label, requiresResult }) => {
          const locked = requiresResult && !result && !loading;
          return (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''} ${locked ? 'nav-item-locked' : ''}`
              }
              title={locked ? 'Run a validation first to unlock this page' : label}
            >
              <span className="nav-icon">
                {locked ? <Lock size={16} /> : <Icon size={18} />}
              </span>
              <span style={{ flex: 1 }}>{label}</span>
              {locked && (
                <span style={{
                  fontSize: 10, color: 'var(--text-muted)',
                  background: 'rgba(255,255,255,0.06)',
                  padding: '2px 6px', borderRadius: 4, fontWeight: 600,
                  letterSpacing: '0.05em',
                }}>
                  VALIDATE FIRST
                </span>
              )}
              {location.pathname === to && !locked && (
                <ChevronRight size={14} style={{ opacity: 0.5 }} />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Validation Status Chip */}
      {result && (
        <div style={{
          margin: '0 12px',
          padding: '12px 16px',
          background: result.is_ready
            ? 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.08))'
            : 'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(220,38,38,0.08))',
          border: `1px solid ${result.is_ready ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
          borderRadius: 12,
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>
            LAST VALIDATION
          </div>
          <div style={{
            fontSize: 12, fontWeight: 700,
            color: result.is_ready ? 'var(--success)' : 'var(--danger)',
            marginBottom: 4,
          }}>
            {result.is_ready ? '✓ Ready for Training' : '✗ Not Ready'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', wordBreak: 'break-all' }}>
            {result.dataset_info?.filename}
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6, marginTop: 8,
          }}>
            <div style={{
              flex: 1, height: 4, background: 'rgba(99,102,241,0.15)',
              borderRadius: 2, overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${result.quality_score?.score ?? 0}%`,
                background: result.quality_score?.score >= 80
                  ? 'var(--success)'
                  : result.quality_score?.score >= 60
                  ? 'var(--warning)'
                  : 'var(--danger)',
                borderRadius: 2,
                transition: 'width 0.8s ease',
              }} />
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>
              {result.quality_score?.score ?? 0}
            </span>
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '11px',
        color: 'var(--text-muted)',
        lineHeight: '1.6',
        marginTop: result ? 12 : 'auto',
      }}>
        <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
          Supported Formats
        </div>
        <div>CSV · Images (ZIP/JPG/PNG)</div>
        <div>Audio (ZIP/WAV/MP3)</div>
        <div>Text (TXT/ZIP)</div>
      </div>
    </aside>
  );
}
