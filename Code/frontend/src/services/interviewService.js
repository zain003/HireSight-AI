/**
 * Live interview API service.
 */
import api from './api';

export const interviewService = {
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
};

export default interviewService;
