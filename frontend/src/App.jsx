import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Layout/Sidebar';
import Upload from './pages/Upload';
import Results from './pages/Results';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Documentation from './pages/Documentation';
import { ValidationProvider } from './context/ValidationContext';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ValidationProvider>
          <div className="app-layout">
            <Sidebar />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Upload />} />
                <Route path="/results" element={<Results />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/history" element={<History />} />
                <Route path="/documentation" element={<Documentation />} />
              </Routes>
            </main>
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              className: 'toast-custom',
              duration: 3000,
              style: {
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
                fontSize: '14px',
              },
              success: {
                iconTheme: { primary: '#10B981', secondary: 'white' },
              },
              error: {
                iconTheme: { primary: '#EF4444', secondary: 'white' },
              },
            }}
          />
        </ValidationProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
