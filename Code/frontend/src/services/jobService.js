import api from './api';

const jobService = {
  getAllJobPosts: async () => {
    const res = await api.get('/auth/admin/job-posts');
    return res.data;
  },
  getJobPost: async (id) => {
    const res = await api.get(`/auth/admin/job-posts/${id}`);
    return res.data;
  },
};

export default jobService;
