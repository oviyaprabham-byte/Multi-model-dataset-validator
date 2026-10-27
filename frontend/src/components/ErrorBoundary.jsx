import React from 'react';

/**
 * ErrorBoundary catches runtime errors in the React component tree,
 * preventing a white screen and showing a user-friendly fallback UI.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[DataValidator] Uncaught error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: 20,
          background: 'var(--bg-primary)',
          padding: 32,
          textAlign: 'center',
        }}>
          {/* Icon */}
          <div style={{
            width: 80, height: 80,
            background: 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(220,38,38,0.1))',
            border: '2px solid rgba(239,68,68,0.4)',
            borderRadius: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 40,
          }}>⚠️</div>

          <div>
            <h1 style={{
              fontSize: 24, fontWeight: 800, color: 'var(--danger)',
              marginBottom: 8, fontFamily: 'Inter, sans-serif',
            }}>
              Something went wrong
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 480 }}>
              An unexpected error occurred in the application. Please refresh the page to continue.
            </p>
          </div>

          {this.state.error && (
            <details style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
              borderRadius: 12, padding: '12px 20px', maxWidth: 560, width: '100%',
              textAlign: 'left',
            }}>
              <summary style={{
                cursor: 'pointer', color: 'var(--text-muted)',
                fontSize: 13, fontWeight: 600, marginBottom: 8,
              }}>
                Error details
              </summary>
              <pre style={{
                fontSize: 11, color: 'var(--danger)', overflowX: 'auto',
                fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}>
                {this.state.error.toString()}
              </pre>
            </details>
          )}

          <button
            onClick={() => window.location.reload()}
            style={{
              background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
              color: 'white', border: 'none', borderRadius: 10,
              padding: '12px 28px', fontSize: 14, fontWeight: 700,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
              boxShadow: '0 4px 15px rgba(99,102,241,0.4)',
              fontFamily: 'Inter, sans-serif',
            }}
          >
            🔄 Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
