import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  UploadCloud, FileText, Image, Music, Table2,
  X, CheckCircle, AlertCircle, Loader2, FileArchive
} from 'lucide-react';
import { validateDataset } from '../services/api';
import { useValidation } from '../context/ValidationContext';

const ACCEPTED = {
  'text/csv': ['.csv'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'audio/wav': ['.wav'],
  'audio/mpeg': ['.mp3'],
  'text/plain': ['.txt'],
  'application/zip': ['.zip'],
  'application/x-zip-compressed': ['.zip'],
};

function getTypeInfo(filename) {
  const ext = filename?.split('.').pop()?.toLowerCase();
  if (ext === 'csv') return { label: 'CSV Dataset', icon: Table2, color: '#6366F1', bg: 'rgba(99,102,241,0.15)' };
  if (['jpg', 'jpeg', 'png'].includes(ext)) return { label: 'Image', icon: Image, color: '#EC4899', bg: 'rgba(236,72,153,0.15)' };
  if (['wav', 'mp3'].includes(ext)) return { label: 'Audio', icon: Music, color: '#F59E0B', bg: 'rgba(245,158,11,0.15)' };
  if (ext === 'txt') return { label: 'Text Dataset', icon: FileText, color: '#10B981', bg: 'rgba(16,185,129,0.15)' };
  if (ext === 'zip') return { label: 'ZIP Archive', icon: FileArchive, color: '#8B5CF6', bg: 'rgba(139,92,246,0.15)' };
  return { label: 'Unknown', icon: FileText, color: '#94A3B8', bg: 'rgba(148,163,184,0.15)' };
}

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const { setResult, setLoading } = useValidation();
  const navigate = useNavigate();

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) {
      setFile(accepted[0]);
      setProgress(0);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    onDropRejected: () => toast.error('Unsupported file type. Please upload CSV, Image, Audio, Text, or ZIP.'),
  });

  const handleValidate = async () => {
    if (!file) {
      toast.error('Please upload a file first.');
      return;
    }
    setUploading(true);
    setLoading(true);
    setProgress(0);

    const toastId = toast.loading('Validating your dataset…');

    try {
      const result = await validateDataset(file, (p) => setProgress(p));
      setResult(result);
      toast.success('Validation complete!', { id: toastId });
      navigate('/results');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Validation failed. Please try again.';
      toast.error(msg, { id: toastId });
    } finally {
      setUploading(false);
      setLoading(false);
    }
  };

  const typeInfo = file ? getTypeInfo(file.name) : null;
  const Icon = typeInfo?.icon || UploadCloud;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Upload Dataset</h1>
          <p className="page-subtitle">Upload your dataset to begin multi-modal validation</p>
        </div>
      </div>

      <div className="page-body">
        {/* Supported types banner */}
        <div className="card animate-fade-in" style={{ padding: '16px 24px' }}>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600 }}>Supported formats:</span>
            {[
              { label: 'CSV', icon: '📊', color: '#6366F1' },
              { label: 'Images (JPG/PNG)', icon: '🖼️', color: '#EC4899' },
              { label: 'Audio (WAV/MP3)', icon: '🎵', color: '#F59E0B' },
              { label: 'Text (TXT)', icon: '📝', color: '#10B981' },
              { label: 'ZIP Archive', icon: '📦', color: '#8B5CF6' },
            ].map((t) => (
              <span key={t.label} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                fontSize: 12, color: t.color, fontWeight: 600,
                background: `${t.color}15`, padding: '4px 12px',
                borderRadius: 20, border: `1px solid ${t.color}30`
              }}>
                <span>{t.icon}</span>{t.label}
              </span>
            ))}
          </div>
        </div>

        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`upload-zone animate-fade-in-delay-1 ${isDragActive ? 'drag-active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="upload-icon">
            {file ? <Icon size={36} color={typeInfo?.color} /> : <UploadCloud size={36} color="var(--accent-light)" />}
          </div>

          {file ? (
            <>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
                File Selected
              </h2>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 10,
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: 12, padding: '12px 20px', marginBottom: 12,
              }}>
                <Icon size={18} color={typeInfo?.color} />
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{file.name}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{humanSize(file.size)}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); setProgress(0); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)', display: 'flex' }}
                >
                  <X size={16} />
                </button>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Click to change file or drag a new one</p>
            </>
          ) : (
            <>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
                {isDragActive ? 'Drop your dataset here!' : 'Drag & Drop your dataset'}
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>
                or click to browse your files
              </p>
              <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                Maximum file size: 500 MB · Supports CSV, Images, Audio, Text, ZIP
              </p>
            </>
          )}
        </div>

        {/* File info card */}
        {file && (
          <div className="card animate-fade-in-delay-2">
            <div className="section-header">
              <div className="section-dot" />
              <span className="section-title">File Information</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }}>
              {[
                { label: 'File Name', value: file.name, icon: '📄' },
                { label: 'File Size', value: humanSize(file.size), icon: '💾' },
                { label: 'Detected Type', value: typeInfo?.label, icon: '🏷️' },
                { label: 'Last Modified', value: new Date(file.lastModified).toLocaleDateString(), icon: '📅' },
              ].map((item) => (
                <div key={item.label} style={{
                  background: 'var(--bg-secondary)',
                  borderRadius: 10,
                  padding: '14px 16px',
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ fontSize: 18, marginBottom: 6 }}>{item.icon}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                    {item.label}
                  </div>
                  <div style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600, wordBreak: 'break-all' }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Progress */}
        {uploading && (
          <div className="card animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 600 }}>
                Uploading & Validating…
              </span>
              <span style={{ fontSize: 14, color: 'var(--accent-light)', fontWeight: 700 }}>
                {progress}%
              </span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, color: 'var(--text-muted)', fontSize: 13 }}>
              <Loader2 size={14} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              Running validation checks…
            </div>
          </div>
        )}

        {/* Validate button */}
        <div className="animate-fade-in-delay-3" style={{ display: 'flex', gap: 12 }}>
          <button
            className="btn btn-primary btn-lg"
            onClick={handleValidate}
            disabled={!file || uploading}
            style={{ opacity: (!file || uploading) ? 0.6 : 1, cursor: (!file || uploading) ? 'not-allowed' : 'pointer' }}
          >
            {uploading ? (
              <>
                <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                Validating…
              </>
            ) : (
              <>
                <CheckCircle size={18} />
                Validate Dataset
              </>
            )}
          </button>

          {file && !uploading && (
            <button className="btn btn-outline" onClick={() => { setFile(null); setProgress(0); }}>
              <X size={16} />
              Clear
            </button>
          )}
        </div>

        {/* How it works */}
        <div className="card animate-fade-in-delay-3">
          <div className="section-header">
            <div className="section-dot" />
            <span className="section-title">How it works</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {[
              { step: '01', title: 'Upload Dataset', desc: 'Drag & drop or browse your dataset file', icon: '📤' },
              { step: '02', title: 'Auto Detection', desc: 'System detects dataset type automatically', icon: '🔍' },
              { step: '03', title: 'Deep Validation', desc: '20+ quality checks run on your data', icon: '✅' },
              { step: '04', title: 'Quality Score', desc: 'Get a 0-100 score with badge rating', icon: '🏆' },
              { step: '05', title: 'Recommendations', desc: 'Actionable fix suggestions generated', icon: '💡' },
              { step: '06', title: 'Download Report', desc: 'Export as PDF or Excel for sharing', icon: '📊' },
            ].map((item) => (
              <div key={item.step} style={{
                padding: '16px',
                background: 'var(--bg-secondary)',
                borderRadius: 10,
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                gap: 12,
                alignItems: 'flex-start',
              }}>
                <div style={{ fontSize: 24, lineHeight: 1 }}>{item.icon}</div>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--accent-light)', fontWeight: 700, letterSpacing: '0.1em', marginBottom: 2 }}>
                    STEP {item.step}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                    {item.title}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
