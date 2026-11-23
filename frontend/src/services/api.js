import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Axios request interceptor: attach Authorization Bearer token automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Axios response interceptor: gracefully catch 401 Unauthorized and purge invalid/expired token
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
    }
    return Promise.reject(error);
  }
);

// Health check API
export const healthCheck = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

// Phase 2 Authentication & Profile APIs
export const loginUser = async (credentials) => {
  const response = await api.post('/api/auth/login', credentials);
  return response.data;
};

export const registerUser = async (userData) => {
  const response = await api.post('/api/auth/register', userData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};

export const updateProfile = async (profileData) => {
  const response = await api.put('/api/auth/profile', profileData);
  return response.data;
};

export const forgotPassword = async (email) => {
  const response = await api.post('/api/auth/forgot-password', { email });
  return response.data;
};

export const resetPassword = async (token, newPassword) => {
  const response = await api.post('/api/auth/reset-password', {
    token,
    new_password: newPassword,
  });
  return response.data;
};

// Phase 3 Resume Analyzer & History APIs
export const analyzeResume = async (formData) => {
  const response = await api.post('/api/resume/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 45000,
  });
  return response.data;
};

export const getResumeHistory = async () => {
  const response = await api.get('/api/resume/history');
  return response.data;
};

export const getResumeAnalysisById = async (analysisId) => {
  const response = await api.get(`/api/resume/${analysisId}`);
  return response.data;
};

export const deleteResumeAnalysis = async (analysisId) => {
  const response = await api.delete(`/api/resume/${analysisId}`);
  return response.data;
};

// Phase 4 AI Interview Question Generator APIs
export const generateInterviewQuestions = async (config) => {
  const response = await api.post('/api/interview/generate-questions', config);
  return response.data;
};

export const getQuestionHistory = async () => {
  const response = await api.get('/api/interview/question-history');
  return response.data;
};

export const getQuestionSet = async (questionSetId) => {
  const response = await api.get(`/api/interview/questions/${questionSetId}`);
  return response.data;
};

export const getInterviewResumeStatus = async () => {
  const response = await api.get('/api/interview/resume-status');
  return response.data;
};

// Phase 5 AI Answer Evaluation & Report APIs
export const evaluateInterviewAnswer = async (payload) => {
  const response = await api.post('/api/interview/evaluate-answer', payload, {
    timeout: 35000,
  });
  return response.data;
};

export const getQuestionEvaluation = async (questionSetId, questionNumber) => {
  const response = await api.get(`/api/interview/evaluation/${questionSetId}/${questionNumber}`);
  return response.data;
};

export const getQuestionSetEvaluations = async (questionSetId) => {
  const response = await api.get(`/api/interview/evaluations/${questionSetId}`);
  return response.data;
};

export const getInterviewFinalReport = async (questionSetId) => {
  const response = await api.get(`/api/interview/report/${questionSetId}`);
  return response.data;
};

export const getInterviewDashboardStats = async () => {
  const response = await api.get('/api/interview/dashboard-stats');
  return response.data;
};

// Phase 6 Performance Analytics & Reports APIs
export const getPerformanceOverview = async (params = {}) => {
  const response = await api.get('/api/performance/overview', { params });
  return response.data;
};

export const getPerformanceTrend = async (params = {}) => {
  const response = await api.get('/api/performance/trend', { params });
  return response.data;
};

export const getSkillPerformance = async (params = {}) => {
  const response = await api.get('/api/performance/skills', { params });
  return response.data;
};

export const getCategoryPerformance = async (params = {}) => {
  const response = await api.get('/api/performance/categories', { params });
  return response.data;
};

export const getRolePerformance = async (params = {}) => {
  const response = await api.get('/api/performance/roles', { params });
  return response.data;
};

export const getInterviewTypePerformance = async (params = {}) => {
  const response = await api.get('/api/performance/types', { params });
  return response.data;
};

export const getPerformanceInsights = async (params = {}) => {
  const response = await api.get('/api/performance/insights', { params });
  return response.data;
};

export const getRecentActivity = async (limit = 6) => {
  const response = await api.get('/api/performance/recent-activity', { params: { limit } });
  return response.data;
};

// Phase 7 Voice Interview & Speech-to-Text APIs
export const startVoiceSession = async (payload) => {
  const response = await api.post('/api/voice-interview/start', payload);
  return response.data;
};

export const submitVoiceAnswer = async (payload) => {
  const response = await api.post('/api/voice-interview/answer', payload, {
    timeout: 35000,
  });
  return response.data;
};

export const submitVoiceNextQuestion = async (payload) => {
  const response = await api.post('/api/voice-interview/next-question', payload, {
    timeout: 35000,
  });
  return response.data;
};

export const getActiveVoiceSession = async () => {
  const response = await api.get('/api/voice-interview/active');
  return response.data;
};

export const getVoiceSession = async (sessionId) => {
  const response = await api.get(`/api/voice-interview/session/${sessionId}`);
  return response.data;
};

export const finishVoiceSession = async (sessionId) => {
  const response = await api.post(`/api/voice-interview/finish/${sessionId}`);
  return response.data;
};

export const getVoiceHistory = async () => {
  const response = await api.get('/api/voice-interview/history');
  return response.data;
};

export const getVoiceReport = async (sessionId) => {
  const response = await api.get(`/api/voice-interview/report/${sessionId}`);
  return response.data;
};

// Aliases matching user prompt names
export const startVoiceInterview = startVoiceSession;
export const getVoiceInterviewSession = getVoiceSession;
export const getVoiceInterviewHistory = getVoiceHistory;
export const getVoiceInterviewReport = getVoiceReport;

// Alias for getInterviewFinalReport matching Phase 6 specification naming
export const getInterviewReport = getInterviewFinalReport;

export default api;

