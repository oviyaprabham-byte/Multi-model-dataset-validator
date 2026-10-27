import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min for large uploads
});

export const validateDataset = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/validate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return response.data;
};

export const getResult = async (sessionId) => {
  const response = await api.get(`/results/${sessionId}`);
  return response.data;
};

export const downloadPDF = async (sessionId) => {
  try {
    const response = await fetch(`/api/report/pdf/${sessionId}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to generate PDF report');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dataset_report_${sessionId.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    throw err;
  }
};

export const downloadExcel = async (sessionId) => {
  try {
    const response = await fetch(`/api/report/excel/${sessionId}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to generate Excel report');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dataset_report_${sessionId.slice(0, 8)}.xlsx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    throw err;
  }
};

export const getHistory = async () => {
  const response = await api.get('/history');
  return response.data;
};

export const deleteHistory = async (sessionId) => {
  await api.delete(`/history/${sessionId}`);
};

export const clearAllHistory = async () => {
  await api.delete('/history');
};

// ── Documentation API ─────────────────────────────────────────────────────────
export const getDocs = async () => {
  const response = await api.get('/docs');
  return response.data;
};

export const getDoc = async (sessionId) => {
  const response = await api.get(`/docs/${sessionId}`);
  return response.data;
};

export const generateDoc = async (sessionId) => {
  const response = await api.post(`/docs/${sessionId}/generate`);
  return response.data;
};

export const deleteDoc = async (sessionId) => {
  await api.delete(`/docs/${sessionId}`);
};

// ── Agent (TTS + Q&A) API ─────────────────────────────────────────────────────
export const getDocText = async (sessionId) => {
  const response = await api.get(`/agent/doc/${sessionId}/text`);
  return response.data;
};

export const askDocQuestion = async (sessionId, question, useLlm = true) => {
  const response = await api.post(`/agent/doc/${sessionId}/ask`, {
    question,
    use_llm: useLlm,
  });
  return response.data;
};

export const getDocChat = async (sessionId) => {
  const response = await api.get(`/agent/chat/${sessionId}`);
  return response.data;
};

export const clearDocChat = async (sessionId) => {
  await api.delete(`/agent/chat/${sessionId}`);
};

export const getAgentStatus = async () => {
  const response = await api.get('/agent/status');
  return response.data;
};

export default api;
