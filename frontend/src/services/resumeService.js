/**
 * Resume API service
 */
import api from './api';

export const resumeService = {
  /**
   * Upload and parse resume
   */
  uploadResume: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/resume/parse', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * Extract skills from text
   */
  extractSkills: async (text, useEmbeddings = true) => {
    const response = await api.post('/resume/extract-skills', {
      text,
      use_embeddings: useEmbeddings,
    });

    return response.data;
  },
};

export default resumeService;
