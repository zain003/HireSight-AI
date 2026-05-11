/**
 * Admin dashboard API (stats, users).
 */
import api from './api';

export const adminDashboardService = {
  getStats: async () => {
    const res = await api.get('/auth/admin/dashboard-stats');
    return res.data;
  },
  getUsers: async () => {
    const res = await api.get('/auth/admin/users');
    return res.data;
  },
};

export default adminDashboardService;
