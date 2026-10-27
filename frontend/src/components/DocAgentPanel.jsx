import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  getDocText, askDocQuestion, getDocChat, clearDocChat
} from '../services/api';
import toast from 'react-hot-toast';
import {
  X, Play, Pause, Square, RotateCcw, Volume2, Send,
  Trash2, Bot, Mic, MessageCircle, ChevronDown, ChevronUp,
  Loader2, Zap
} from 'lucide-react';

// ── Helpers ────────────────────────────────────────────────────────────────────
function splitIntoSections(text) {
  // Split on ## headings to create sections for progress display
  const parts = text.split(/\n## /);
  return parts.map((p, i) => (i === 0 ? p : '## ' + p));
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function DocAgentPanel({ sessionId, datasetName, onClose }) {
  // TTS state
  const [docText, setDocText]           = useState('');
  const [sections, setSections]         = useState([]);
  const [ttsLoading, setTtsLoading]     = useState(true);
  const [ttsStatus, setTtsStatus]       = useState('idle'); // idle | playing | paused | done
  const [currentSection, setCurrentSection] = useState(0);
  const [speed, setSpeed]               = useState(1.0);

  // Chat state
  const [messages, setMessages]         = useState([]);
  const [question, setQuestion]         = useState('');
  const [asking, setAsking]             = useState(false);
  const [chatVisible, setChatVisible]   = useState(true);

  // Refs
  const utteranceRef  = useRef(null);
  const chatBottomRef = useRef(null);
  const inputRef      = useRef(null);

  // ── Load doc text and chat history ──────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    const loadData = async () => {
      setTtsLoading(true);
      try {
        const [textData, chatData] = await Promise.all([
          getDocText(sessionId),
          getDocChat(sessionId),
        ]);
        if (cancelled) return;
        setDocText(textData.text || '');
        setSections(splitIntoSections(textData.text || ''));
        setMessages(chatData.messages || []);
      } catch (err) {
        if (!cancelled) toast.error('Failed to load documentation text');
      } finally {
        if (!cancelled) setTtsLoading(false);
      }
    };

    loadData();
    return () => {
      cancelled = true;
      window.speechSynthesis.cancel();
    };
  }, [sessionId]);

  // Scroll chat to bottom when new messages arrive
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // ── TTS Controls ─────────────────────────────────────────────────────────────
  const speak = useCallback((sectionIndex = 0) => {
    window.speechSynthesis.cancel();
    if (!docText) return;

    const textToSpeak = sections.length > 0
      ? sections.slice(sectionIndex).join('\n\n')
      : docText;

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = speed;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setTtsStatus('playing');
      setCurrentSection(sectionIndex);
    };

    utterance.onend = () => {
      setTtsStatus('done');
      setCurrentSection(sections.length);
    };

    utterance.onerror = (e) => {
      if (e.error !== 'interrupted') {
        setTtsStatus('idle');
        toast.error(`Voice error: ${e.error}`);
      }
    };

    // Track section progress by word boundary (best-effort)
    utterance.onboundary = (e) => {
      if (e.name === 'sentence' && sections.length > 0) {
        // Estimate which section we're in based on char index
        let charCount = 0;
        for (let i = sectionIndex; i < sections.length; i++) {
          charCount += sections[i].length + 2; // +2 for '\n\n'
          if (e.charIndex < charCount) {
            setCurrentSection(i);
            break;
          }
        }
      }
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setTtsStatus('playing');
  }, [docText, sections, speed]);

  const handlePlay = () => {
    if (ttsStatus === 'paused') {
      window.speechSynthesis.resume();
      setTtsStatus('playing');
    } else {
      speak(0);
    }
  };

  const handlePause = () => {
    window.speechSynthesis.pause();
    setTtsStatus('paused');
  };

  const handleStop = () => {
    window.speechSynthesis.cancel();
    setTtsStatus('idle');
    setCurrentSection(0);
  };

  const handleReplay = () => {
    setCurrentSection(0);
    speak(0);
  };

  // Update speed on change (requires restart if playing)
  const handleSpeedChange = (newSpeed) => {
    setSpeed(newSpeed);
    if (ttsStatus === 'playing') {
      speak(currentSection);
    }
  };

  // ── Q&A ──────────────────────────────────────────────────────────────────────
  const handleAsk = async (e) => {
    e?.preventDefault();
    const q = question.trim();
    if (!q || asking) return;

    const userMsg = { role: 'user', content: q, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setQuestion('');
    setAsking(true);

    try {
      const data = await askDocQuestion(sessionId, q);
      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        timestamp: data.timestamp,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      toast.error('Failed to get answer');
      setMessages(prev => prev.filter(m => m !== userMsg));
    } finally {
      setAsking(false);
      inputRef.current?.focus();
    }
  };

  const handleClearChat = async () => {
    try {
      await clearDocChat(sessionId);
      setMessages([]);
      toast.success('Chat cleared');
    } catch {
      toast.error('Failed to clear chat');
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────────
  const progressPct = sections.length > 0
    ? Math.round((currentSection / sections.length) * 100)
    : 0;

  return (
    <>
      {/* Overlay */}
      <div
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(3px)', zIndex: 200,
        }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0,
        width: 'min(480px, 100vw)',
        background: 'var(--bg-card)',
        borderLeft: '1px solid var(--border)',
        zIndex: 201,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-12px 0 48px rgba(0,0,0,0.4)',
        animation: 'slideInRight 0.3s ease',
      }}>

        {/* Header */}
        <div style={{
          padding: '20px 24px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <Bot size={18} color="white" />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>
                AI Dataset Agent
              </div>
              <div style={{
                fontSize: 12, color: 'var(--text-muted)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {datasetName}
              </div>
            </div>
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border-subtle)',
                borderRadius: 8, padding: '6px', cursor: 'pointer',
                color: 'var(--text-muted)', display: 'flex', alignItems: 'center',
              }}
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Scrollable body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* ── Voice Reading Section ─────────────────────────────────────── */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Volume2 size={16} color="#a78bfa" />
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                Voice Reading
              </span>
              <span className="badge" style={{
                marginLeft: 'auto', fontSize: 10,
                background: ttsStatus === 'playing' ? 'rgba(16,185,129,0.15)' : 'rgba(99,102,241,0.15)',
                color: ttsStatus === 'playing' ? 'var(--success)' : 'var(--accent-light)',
                border: `1px solid ${ttsStatus === 'playing' ? 'rgba(16,185,129,0.3)' : 'rgba(99,102,241,0.3)'}`,
              }}>
                {ttsStatus === 'idle' && 'Ready'}
                {ttsStatus === 'playing' && '▶ Playing'}
                {ttsStatus === 'paused' && '⏸ Paused'}
                {ttsStatus === 'done' && '✓ Done'}
              </span>
            </div>

            {ttsLoading ? (
              <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>
                <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 8px' }} />
                <div style={{ fontSize: 13 }}>Loading documentation text…</div>
              </div>
            ) : (
              <>
                {/* Progress */}
                {sections.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      fontSize: 11, color: 'var(--text-muted)', marginBottom: 6,
                    }}>
                      <span>Section {Math.min(currentSection + 1, sections.length)} of {sections.length}</span>
                      <span>{progressPct}%</span>
                    </div>
                    <div style={{
                      height: 4, background: 'rgba(99,102,241,0.15)', borderRadius: 2, overflow: 'hidden',
                    }}>
                      <div style={{
                        height: '100%', width: `${progressPct}%`,
                        background: 'linear-gradient(90deg, #6366f1, #a78bfa)',
                        borderRadius: 2, transition: 'width 0.4s ease',
                      }} />
                    </div>
                  </div>
                )}

                {/* Controls */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={handlePlay}
                    disabled={ttsStatus === 'playing'}
                    style={{ flex: 1, minWidth: 70 }}
                  >
                    <Play size={13} />
                    {ttsStatus === 'paused' ? 'Resume' : 'Play'}
                  </button>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={handlePause}
                    disabled={ttsStatus !== 'playing'}
                    style={{ flex: 1, minWidth: 70 }}
                  >
                    <Pause size={13} /> Pause
                  </button>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={handleStop}
                    disabled={ttsStatus === 'idle'}
                    style={{ flex: 1, minWidth: 70 }}
                  >
                    <Square size={13} /> Stop
                  </button>
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={handleReplay}
                    style={{ flex: 1, minWidth: 70 }}
                    title="Replay from beginning"
                  >
                    <RotateCcw size={13} /> Replay
                  </button>
                </div>

                {/* Speed */}
                <div>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    fontSize: 11, color: 'var(--text-muted)', marginBottom: 6,
                  }}>
                    <span>Speed</span>
                    <span style={{ fontWeight: 700, color: 'var(--accent-light)' }}>{speed.toFixed(1)}×</span>
                  </div>
                  <input
                    type="range"
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    value={speed}
                    onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                    style={{
                      width: '100%', accentColor: '#6366f1', cursor: 'pointer',
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
                    <span>0.5×</span><span>1.0×</span><span>1.5×</span><span>2.0×</span>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* ── Q&A Chat Section ──────────────────────────────────────────── */}
          <div className="card" style={{ padding: 20, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div
              style={{
                display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16,
                cursor: 'pointer', userSelect: 'none',
              }}
              onClick={() => setChatVisible(v => !v)}
            >
              <MessageCircle size={16} color="#a78bfa" />
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', flex: 1 }}>
                Ask a Question
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {messages.length} message{messages.length !== 1 ? 's' : ''}
              </span>
              {messages.length > 0 && (
                <button
                  className="btn btn-outline btn-sm"
                  style={{ padding: '3px 8px', fontSize: 10, color: 'var(--danger)' }}
                  onClick={(e) => { e.stopPropagation(); handleClearChat(); }}
                  title="Clear chat"
                >
                  <Trash2 size={11} />
                </button>
              )}
              {chatVisible ? <ChevronUp size={14} color="var(--text-muted)" /> : <ChevronDown size={14} color="var(--text-muted)" />}
            </div>

            {chatVisible && (
              <>
                {/* Messages */}
                <div style={{
                  flex: 1, overflowY: 'auto', marginBottom: 12,
                  maxHeight: 320, minHeight: 80,
                  display: 'flex', flexDirection: 'column', gap: 10,
                }}>
                  {messages.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-muted)', fontSize: 13 }}>
                      <Zap size={28} style={{ margin: '0 auto 8px', opacity: 0.3 }} />
                      <div>Ask anything about this dataset</div>
                      <div style={{ fontSize: 11, marginTop: 4 }}>
                        Quality score • Issues • Recommendations • ML algorithm • Missing values…
                      </div>
                    </div>
                  ) : (
                    messages.map((msg, i) => (
                      <div key={i} style={{
                        display: 'flex',
                        justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      }}>
                        <div style={{
                          maxWidth: '85%',
                          padding: '10px 14px',
                          borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                          background: msg.role === 'user'
                            ? 'linear-gradient(135deg, #6366f1, #7c3aed)'
                            : 'rgba(255,255,255,0.06)',
                          border: msg.role === 'user'
                            ? 'none'
                            : '1px solid var(--border-subtle)',
                          color: 'var(--text-primary)',
                          fontSize: 13,
                          lineHeight: 1.5,
                          whiteSpace: 'pre-wrap',
                        }}>
                          {msg.role === 'assistant' && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                              <Bot size={12} color="#a78bfa" />
                              <span style={{ fontSize: 10, color: '#a78bfa', fontWeight: 600 }}>AI Agent</span>
                            </div>
                          )}
                          {msg.content}
                        </div>
                      </div>
                    ))
                  )}
                  {asking && (
                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                      <div style={{
                        padding: '10px 14px',
                        borderRadius: '16px 16px 16px 4px',
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid var(--border-subtle)',
                        display: 'flex', alignItems: 'center', gap: 8,
                      }}>
                        <div className="loading-spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Thinking…</span>
                      </div>
                    </div>
                  )}
                  <div ref={chatBottomRef} />
                </div>

                {/* Input */}
                <form onSubmit={handleAsk} style={{ display: 'flex', gap: 8 }}>
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder="Ask about this dataset…"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={asking}
                    style={{
                      flex: 1,
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border)',
                      borderRadius: 10,
                      padding: '10px 14px',
                      color: 'var(--text-primary)',
                      fontSize: 13,
                      outline: 'none',
                    }}
                    onFocus={e => e.target.style.borderColor = 'rgba(99,102,241,0.5)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border)'}
                  />
                  <button
                    type="submit"
                    className="btn btn-primary btn-sm"
                    disabled={!question.trim() || asking}
                    style={{ padding: '10px 14px', borderRadius: 10 }}
                  >
                    <Send size={14} />
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
