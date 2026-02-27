/**
 * Interview API service (Module 2 - Future)
 */
import api from './api';

export const interviewService = {
  /**
   * Start a new interview session
   */
  startSession: async (sessionData) => {
    const response = await api.post('/auth/start-session', sessionData);
    return response.data;
  },

  /**
   * Get user's interview sessions
   */
  getSessions: async () => {
    const response = await api.get('/auth/sessions');
    return response.data;
  },

  /**
   * Get questions for a session (Module 2)
   */
  getQuestions: async (sessionId) => {
    const response = await api.get(`/interview/questions/${sessionId}`);
    return response.data;
  },

  /**
   * Submit answer (Module 2)
   */
  submitAnswer: async (sessionId, questionId, answer) => {
    const response = await api.post(`/interview/answer`, {
      session_id: sessionId,
      question_id: questionId,
      answer,
    });
    return response.data;
  },
};

export default interviewService;
