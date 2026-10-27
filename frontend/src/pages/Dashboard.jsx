import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useValidation } from '../context/ValidationContext';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, Legend
} from 'recharts';
import { UploadCloud } from 'lucide-react';

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12, color: 'var(--text-primary)',
    }}>
      {label && <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || p.fill }}>
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { result } = useValidation();
  const navigate = useNavigate();

  if (!result) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 16 }}>
        <UploadCloud size={64} color="var(--text-muted)" />
        <h2 style={{ color: 'var(--text-secondary)', fontSize: 20 }}>No data to display</h2>
        <p style={{ color: 'var(--text-muted)' }}>Upload and validate a dataset first to see the dashboard</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          <UploadCloud size={16} /> Upload Dataset
        </button>
      </div>
    );
  }

  const { quality_score, dataset_info, checks, issues, dashboard_data, is_ready } = result;

  // Build chart data
  const statusData = [
    { name: 'Passed', value: checks.filter(c => c.status === 'pass').length, color: '#10B981' },
    { name: 'Failed', value: checks.filter(c => c.status === 'fail').length, color: '#EF4444' },
    { name: 'Warning', value: checks.filter(c => c.status === 'warning').length, color: '#F59E0B' },
  ].filter(d => d.value > 0);

  const severityData = [
    { name: 'High', value: issues.filter(i => i.severity === 'high').length, color: '#EF4444' },
    { name: 'Medium', value: issues.filter(i => i.severity === 'medium').length, color: '#F59E0B' },
    { name: 'Low', value: issues.filter(i => i.severity === 'low').length, color: '#10B981' },
  ].filter(d => d.value > 0);

  const classDistData = Object.entries(dashboard_data?.class_distribution || {}).map(([k, v], i) => ({
    name: k.length > 12 ? k.slice(0, 12) + '…' : k,
    count: v,
    fill: COLORS[i % COLORS.length],
  }));

  const missingPerCol = (dashboard_data?.missing_per_column || []).slice(0, 10).map((m, i) => ({
    name: m.column?.length > 10 ? m.column.slice(0, 10) + '…' : m.column,
    missing: m.missing,
    fill: COLORS[i % COLORS.length],
  }));

  const formatDist = Object.entries(dashboard_data?.format_distribution || {}).map(([k, v], i) => ({
    name: k.toUpperCase(),
    value: v,
    color: COLORS[i % COLORS.length],
  }));

  const scoreBreakdown = Object.entries(quality_score.breakdown).map(([k, v]) => ({
    name: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    score: v,
    fill: v >= 15 ? '#10B981' : v >= 8 ? '#F59E0B' : '#EF4444',
  }));

  const statCards = [
    {
      label: 'Quality Score',
      value: `${quality_score.score}/100`,
      sub: quality_score.badge,
      icon: '🏆',
      bg: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.1))',
      color: '#6366F1',
    },
    {
      label: 'Total Files/Rows',
      value: dataset_info.total_files ?? dataset_info.total_rows ?? '—',
      sub: dataset_info.dataset_type?.toUpperCase(),
      icon: '📁',
      bg: 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.1))',
      color: '#10B981',
    },
    {
      label: 'Issues Found',
      value: issues.length,
      sub: `${issues.filter(i => i.severity === 'high').length} high severity`,
      icon: '⚠️',
      bg: 'linear-gradient(135deg, rgba(245,158,11,0.2), rgba(217,119,6,0.1))',
      color: '#F59E0B',
    },
    {
      label: 'Training Status',
      value: is_ready ? 'READY' : 'NOT READY',
      sub: is_ready ? 'All checks passed' : 'Fix issues first',
      icon: is_ready ? '✅' : '❌',
      bg: is_ready
        ? 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.1))'
        : 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(220,38,38,0.1))',
      color: is_ready ? '#10B981' : '#EF4444',
    },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics Dashboard</h1>
          <p className="page-subtitle">{dataset_info.filename} · {dataset_info.dataset_type?.toUpperCase()} Dataset</p>
        </div>
      </div>

      <div className="page-body">

        {/* Stat Cards Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          {statCards.map((s) => (
            <div key={s.label} className="stat-card animate-fade-in" style={{ background: s.bg, border: `1px solid ${s.color}30` }}>
              <div className="stat-icon" style={{ background: `${s.color}20`, fontSize: 22 }}>{s.icon}</div>
              <div>
                <div className="stat-value" style={{ color: s.color, fontSize: 22 }}>{s.value}</div>
                <div className="stat-label" style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600 }}>{s.label}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.sub}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Row 1 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>

          {/* Validation Status Pie */}
          <div className="card animate-fade-in-delay-1">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Validation Status</span>
            </div>
            {statusData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={statusData} dataKey="value" cx="50%" cy="50%" outerRadius={75} innerRadius={40} paddingAngle={3}>
                    {statusData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No data</div>
            )}
          </div>

          {/* Issue Severity Pie */}
          <div className="card animate-fade-in-delay-1">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Issue Severity</span>
            </div>
            {severityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={severityData} dataKey="value" cx="50%" cy="50%" outerRadius={75} innerRadius={40} paddingAngle={3}>
                    {severityData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--success)', padding: 40, fontSize: 14, fontWeight: 600 }}>
                🎉 No Issues!
              </div>
            )}
          </div>

          {/* Format Distribution Pie */}
          <div className="card animate-fade-in-delay-1">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Format Distribution</span>
            </div>
            {formatDist.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={formatDist} dataKey="value" cx="50%" cy="50%" outerRadius={75} innerRadius={40} paddingAngle={3}>
                    {formatDist.map((entry, i) => (
                      <Cell key={i} fill={entry.color} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40, fontSize: 13 }}>
                Single format dataset
              </div>
            )}
          </div>
        </div>

        {/* Charts Row 2 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* Class Distribution Bar */}
          {classDistData.length > 0 && (
            <div className="card animate-fade-in-delay-2">
              <div className="section-header">
                <div className="section-dot" />
                <span className="section-title">Class Distribution</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={classDistData} margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {classDistData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Missing Values Bar */}
          {missingPerCol.length > 0 && (
            <div className="card animate-fade-in-delay-2">
              <div className="section-header">
                <div className="section-dot" />
                <span className="section-title">Missing Values per Column</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={missingPerCol} margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="missing" radius={[6, 6, 0, 0]}>
                    {missingPerCol.map((entry, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Score Breakdown Radial */}
          <div className="card animate-fade-in-delay-2" style={{ gridColumn: classDistData.length === 0 && missingPerCol.length === 0 ? '1 / 3' : 'auto' }}>
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">Quality Score Breakdown</span>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <RadialBarChart
                cx="50%" cy="50%"
                innerRadius="20%"
                outerRadius="90%"
                barSize={14}
                data={scoreBreakdown}
                startAngle={90}
                endAngle={-270}
              >
                <RadialBar
                  minAngle={10}
                  dataKey="score"
                  cornerRadius={6}
                  background={{ fill: 'rgba(99,102,241,0.05)' }}
                />
                <Legend
                  iconSize={10}
                  layout="vertical"
                  verticalAlign="middle"
                  align="right"
                  formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{v}</span>}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
