/**
 * Admin dashboard API (stats, users, report exports).
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
  getReportJson: async (sessionId) => {
    const res = await api.get(`/interview/admin/session/${sessionId}/export/json`);
    return res.data;
  },
  downloadReportPdf: async (sessionId, filename = null) => {
    const res = await api.get(`/interview/admin/session/${sessionId}/export/pdf`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || `recruiter_report_${sessionId}.pdf`);
    document.body.appendChild(link);
    link.click();
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    window.URL.revokeObjectURL(url);
    return true;
  },
  exportReportJson: async (sessionId, filename = null) => {
    const res = await api.get(`/interview/admin/session/${sessionId}/export/json`);
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(res.data, null, 2));
    const link = document.createElement('a');
    link.setAttribute('href', dataStr);
    link.setAttribute('download', filename || `recruiter_report_${sessionId}.json`);
    document.body.appendChild(link);
    link.click();
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    return res.data;
  },
};

export default adminDashboardService;
