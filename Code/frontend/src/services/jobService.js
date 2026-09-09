import api from './api';

const jobService = {
  getAllJobPosts: async () => {
    const res = await api.get('/auth/jobs');
    return res.data;
  },
  getJobPost: async (id) => {
    const res = await api.get(`/auth/jobs/${id}`);
    return res.data;
  },
};

export default jobService;
