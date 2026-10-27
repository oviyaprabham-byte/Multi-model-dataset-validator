import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useValidation } from '../context/ValidationContext';
import { downloadPDF, downloadExcel } from '../services/api';
import toast from 'react-hot-toast';
import {
  CheckCircle2, XCircle, AlertTriangle, Download,
  FileText, Table2, UploadCloud, ArrowRight,
  TrendingUp, AlertCircle, Lightbulb, ShieldCheck, ShieldX
} from 'lucide-react';

function StatusIcon({ status, size = 16 }) {
  if (status === 'pass') return <CheckCircle2 size={size} color="var(--success)" />;
  if (status === 'fail') return <XCircle size={size} color="var(--danger)" />;
  return <AlertTriangle size={size} color="var(--warning)" />;
}

function SeverityBadge({ severity }) {
  const map = {
    high: 'badge-danger',
    medium: 'badge-warning',
    low: 'badge-success',
  };
  return <span className={`badge ${map[severity] || 'badge-accent'}`}>{severity?.toUpperCase()}</span>;
}

function ScoreGauge({ score, badge }) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const dash = (score / 100) * circumference;
  const badgeColors = {
    Excellent: '#10B981',
    Good: '#6366F1',
    Average: '#F59E0B',
    Poor: '#EF4444',
  };
  const color = badgeColors[badge] || '#6366F1';

  return (
    <div style={{ position: 'relative', width: 180, height: 180, margin: '0 auto' }}>
      <svg width="180" height="180" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="90" cy="90" r={radius} fill="none" stroke="rgba(99,102,241,0.1)" strokeWidth="12" />
        <circle
          cx="90" cy="90" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease', filter: `drop-shadow(0 0 8px ${color}50)` }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ fontSize: 36, fontWeight: 900, color: 'var(--text-primary)', lineHeight: 1 }}>
          {score}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>/ 100</div>
        <div style={{ fontSize: 13, color, fontWeight: 700, marginTop: 4 }}>{badge}</div>
      </div>
    </div>
  );
}

function ScoreBreakdownBar({ label, value, maxValue, color }) {
  const pct = (value / maxValue) * 100;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
          {label.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: 12, fontWeight: 700, color }}>
          {value}/{maxValue}
        </span>
      </div>
      <div className="progress-bar" style={{ height: 4 }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: pct >= 70 ? 'var(--success)' : pct >= 40 ? 'var(--warning)' : 'var(--danger)',
          borderRadius: 2,
          transition: 'width 0.8s ease',
        }} />
      </div>
    </div>
  );
}

export default function Results() {
  const { result } = useValidation();
  const navigate = useNavigate();

  if (!result) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 16 }}>
        <UploadCloud size={64} color="var(--text-muted)" />
        <h2 style={{ color: 'var(--text-secondary)', fontSize: 20 }}>No validation results yet</h2>
        <p style={{ color: 'var(--text-muted)' }}>Upload a dataset to see validation results here</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          <UploadCloud size={16} /> Go to Upload
        </button>
      </div>
    );
  }

  const { dataset_info, checks, issues, recommendations, quality_score, is_ready, readiness_reasons, session_id, timestamp } = result;

  const maxMap = { missing_values: 20, duplicates: 15, corrupted: 25, empty: 15, format: 10, class_imbalance: 10, missing_labels: 5 };
  const badgeClass = {
    Excellent: 'badge-excellent',
    Good: 'badge-good',
    Average: 'badge-average',
    Poor: 'badge-poor',
  }[quality_score.badge] || 'badge-accent';

  const passCount = checks.filter(c => c.status === 'pass').length;
  const failCount = checks.filter(c => c.status === 'fail').length;
  const warnCount = checks.filter(c => c.status === 'warning').length;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Validation Results</h1>
          <p className="page-subtitle">
            {dataset_info.filename} · {timestamp}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="btn btn-outline btn-sm" onClick={() => downloadPDF(session_id)}>
            <Download size={14} /> PDF Report
          </button>
          <button className="btn btn-success btn-sm" onClick={() => downloadExcel(session_id)}>
            <Table2 size={14} /> Excel Report
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/')}>
            <UploadCloud size={14} /> New Upload
          </button>
        </div>
      </div>

      <div className="page-body">

        {/* Readiness Banner */}
        <div className={`animate-fade-in ${is_ready ? 'readiness-ready' : 'readiness-notready'}`}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: is_ready ? 0 : 16 }}>
            {is_ready
              ? <ShieldCheck size={40} color="var(--success)" />
              : <ShieldX size={40} color="var(--danger)" />
            }
            <div>
              <div style={{
                fontSize: 28, fontWeight: 900,
                color: is_ready ? 'var(--success)' : 'var(--danger)',
                letterSpacing: '-0.02em',
              }}>
                {is_ready ? '✓ READY FOR TRAINING' : '✗ NOT READY FOR TRAINING'}
              </div>
              {is_ready && (
                <div style={{ fontSize: 14, color: 'var(--text-muted)', marginTop: 4 }}>
                  Dataset satisfies all critical validation requirements.
                </div>
              )}
            </div>
          </div>

          {!is_ready && readiness_reasons.length > 0 && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', borderRadius: 10, padding: 16,
              border: '1px solid rgba(239,68,68,0.2)', textAlign: 'left',
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--danger)', marginBottom: 8 }}>
                Issues to resolve:
              </div>
              {readiness_reasons.map((r, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6 }}>
                  <XCircle size={14} color="var(--danger)" style={{ marginTop: 1, flexShrink: 0 }} />
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{r}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Score + Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
          {/* Quality Score Card */}
          <div className="card animate-fade-in-delay-1" style={{ gridColumn: '1', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <div className="section-header" style={{ width: '100%' }}>
              <div className="section-dot" />
              <span className="section-title">Quality Score</span>
            </div>
            <ScoreGauge score={quality_score.score} badge={quality_score.badge} />
            <span className={`badge ${badgeClass}`} style={{ fontSize: 14, padding: '6px 16px' }}>
              {quality_score.badge}
            </span>
          </div>

          {/* Score Breakdown */}
          <div className="card animate-fade-in-delay-1">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Score Breakdown</span>
            </div>
            {Object.entries(quality_score.breakdown).map(([dim, val]) => (
              <ScoreBreakdownBar
                key={dim}
                label={dim}
                value={val}
                maxValue={maxMap[dim] || 10}
                color={val >= (maxMap[dim] || 10) * 0.7 ? 'var(--success)' : val >= (maxMap[dim] || 10) * 0.4 ? 'var(--warning)' : 'var(--danger)'}
              />
            ))}
          </div>

          {/* Check Summary */}
          <div className="card animate-fade-in-delay-1">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Check Summary</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'Passed', count: passCount, color: 'var(--success)', bg: 'var(--success-bg)', icon: '✓' },
                { label: 'Failed', count: failCount, color: 'var(--danger)', bg: 'var(--danger-bg)', icon: '✗' },
                { label: 'Warnings', count: warnCount, color: 'var(--warning)', bg: 'var(--warning-bg)', icon: '⚠' },
                { label: 'Total Issues', count: issues.length, color: 'var(--accent-light)', bg: 'rgba(99,102,241,0.1)', icon: '📋' },
              ].map((item) => (
                <div key={item.label} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '10px 14px', background: item.bg, borderRadius: 8,
                  border: `1px solid ${item.color}20`,
                }}>
                  <span style={{ fontSize: 13, color: item.color, fontWeight: 600 }}>
                    {item.icon} {item.label}
                  </span>
                  <span style={{ fontSize: 22, fontWeight: 900, color: item.color }}>
                    {item.count}
                  </span>
                </div>
              ))}
            </div>

            {/* Dataset Info */}
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                Dataset Info
              </div>
              {[
                ['Type', dataset_info.dataset_type?.toUpperCase()],
                ['Size', dataset_info.size_human],
                dataset_info.total_rows && ['Rows', dataset_info.total_rows.toLocaleString()],
                dataset_info.total_columns && ['Columns', dataset_info.total_columns],
                dataset_info.total_files && ['Files', dataset_info.total_files.toLocaleString()],
              ].filter(Boolean).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{k}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Validation Checks Table */}
        <div className="card animate-fade-in-delay-2">
          <div className="section-header">
            <div className="section-dot" />
            <span className="section-title">Validation Checks</span>
            <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
              {checks.length} checks performed
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Check</th>
                  <th>Status</th>
                  <th>Message</th>
                  <th>Severity</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {checks.map((check, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{check.name}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <StatusIcon status={check.status} />
                        <span style={{
                          fontSize: 12, fontWeight: 600,
                          color: check.status === 'pass' ? 'var(--success)' : check.status === 'fail' ? 'var(--danger)' : 'var(--warning)',
                        }}>
                          {check.status?.toUpperCase()}
                        </span>
                      </div>
                    </td>
                    <td>{check.message}</td>
                    <td>{check.severity ? <SeverityBadge severity={check.severity} /> : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>}</td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--accent-light)' }}>
                      {check.value !== undefined && check.value !== null ? String(check.value) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Issues + Recommendations */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* Issues */}
          <div className="card animate-fade-in-delay-2">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Issues Found</span>
              {issues.length > 0 && (
                <span className="badge badge-danger" style={{ marginLeft: 'auto' }}>
                  {issues.length} issue{issues.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            {issues.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={32} color="var(--success)" style={{ margin: '0 auto 8px' }} />
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--success)' }}>No issues found!</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {issues.map((issue, i) => (
                  <div key={i} style={{
                    padding: '12px 14px',
                    background: issue.severity === 'high' ? 'var(--danger-bg)' : issue.severity === 'medium' ? 'var(--warning-bg)' : 'var(--success-bg)',
                    border: `1px solid ${issue.severity === 'high' ? 'rgba(239,68,68,0.2)' : issue.severity === 'medium' ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)'}`,
                    borderRadius: 10,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                        {issue.count ? `${issue.count} ` : ''}{issue.title}
                      </span>
                      <SeverityBadge severity={issue.severity} />
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{issue.description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommendations */}
          <div className="card animate-fade-in-delay-3">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Recommendations</span>
              <span className="badge badge-accent" style={{ marginLeft: 'auto' }}>
                {recommendations.length} tip{recommendations.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {recommendations.map((rec, i) => (
                <div key={i} className="rec-item">
                  <div className="rec-number">{i + 1}</div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{rec.title}</span>
                      <SeverityBadge severity={rec.priority} />
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>{rec.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Download Report */}
        <div className="card animate-fade-in-delay-3" style={{
          background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.04))',
          border: '1px solid rgba(99,102,241,0.2)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                📊 Download Full Report
              </h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Get a comprehensive report with all validation details, quality scores, and recommendations.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button className="btn btn-primary" onClick={() => {
                downloadPDF(session_id);
                toast.success('Downloading PDF report…');
              }}>
                <FileText size={16} /> Download PDF
              </button>
              <button className="btn btn-success" onClick={() => {
                downloadExcel(session_id);
                toast.success('Downloading Excel report…');
              }}>
                <Table2 size={16} /> Download Excel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
