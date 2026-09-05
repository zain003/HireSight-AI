/**
 * Live interview API service.
 */
import api from './api';

export const interviewService = {
  /**
   * Fetch standardized tech roles and competency mappings.
   */
  getRoleConfigs: async (experienceYears = null) => {
    const params = experienceYears !== null ? { experience_years: experienceYears } : {};
    const response = await api.get('/interview/config/roles', { params });
    return response.data;
  },

  /**
   * Analyze candidate skill overlap and role fit for a selected role.
   */
  getRoleFit: async (role, skills = [], yearsExperience = null) => {
    const response = await api.post('/interview/config/role-fit', {
      role,
      skills,
      ...(yearsExperience !== null ? { years_experience: yearsExperience } : {}),
    });
    return response.data;
  },

  startSession: async (payload) => {
    const response = await api.post('/interview/live/start', payload);
    return response.data;
  },

  /**
   * Get user's interview sessions
   */
  getSessions: async () => {
    const response = await api.get('/auth/sessions');
    return response.data;
  },

  submitAnswer: async (sessionId, payload) => {
    const response = await api.post(`/interview/live/${sessionId}/answer`, payload);
    return response.data;
  },

  /**
   * Fetch current session state for recovery on page reload or synchronization.
   */
  getSessionState: async (sessionId) => {
    const response = await api.get(`/interview/live/${sessionId}/state`);
    return response.data;
  },

  fetchSessionState: async (sessionId) => {
    const response = await api.get(`/interview/live/${sessionId}/state`);
    return response.data;
  },

  registerFace: async (sessionId, imageBase64) => {
    const response = await api.post(`/interview/live/${sessionId}/register-face`, {
      image_base64: imageBase64,
    });
    return response.data;
  },

  verifyFace: async (sessionId, imageBase64) => {
    const response = await api.post(`/interview/live/${sessionId}/verify-face`, {
      image_base64: imageBase64,
    });
    return response.data;
  },

  analyzeFrame: async (sessionId, frameBase64List = []) => {
    const response = await api.post(`/interview/live/${sessionId}/analyze-frame`, {
      frame_base64_list: frameBase64List,
    });
    return response.data;
  },

  endSession: async (sessionId) => {
    const response = await api.post(`/interview/live/${sessionId}/end`);
    return response.data;
  },

  getReport: async (sessionId) => {
    const response = await api.get(`/interview/live/${sessionId}/report`);
    return response.data;
  },

  tts: async (text, options = {}) => {
    const response = await api.post('/interview/live/tts', {
      text,
      ...options,
    });
    return response.data;
  },

  /**
   * Run candidate code locally against public stdin/stdout tests (backend subprocess sandbox).
   */
  runPublicCode: async (payload) => {
    const response = await api.post('/interview/coding/run-public', payload);
    return response.data;
  },

  /**
   * Run candidate code locally (backward compatible alias).
   */
  runCode: async (payload) => {
    const response = await api.post('/interview/coding/run-public', payload);
    return response.data;
  },

  /**
   * Submit candidate coding challenge solution for server-side evaluation against public & hidden suites.
   */
  submitCodingChallenge: async (sessionId, payload) => {
    const response = await api.post(`/interview/live/${sessionId}/submit-coding-challenge`, payload);
    return response.data;
  },

  /**
   * Live speech-to-text audio stream transcription via backend Whisper AI.
   */
  transcribeAudio: async (audioBase64, audioFormat = 'webm', language = 'en') => {
    const response = await api.post('/interview/live/transcribe', {
      audio_base64: audioBase64,
      audio_format: audioFormat,
      language,
    });
    return response.data?.text || '';
  },
};

export default interviewService;
