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
  getCandidateRoster: async (params = {}) => {
    // Clean up empty params
    const cleanParams = {};
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          if (value.length > 0) {
            cleanParams[key] = value;
          }
        } else {
          cleanParams[key] = value;
        }
      }
    });

    const res = await api.get('/auth/admin/candidates', {
      params: cleanParams,
      paramsSerializer: (paramsObj) => {
        const searchParams = new URLSearchParams();
        Object.entries(paramsObj).forEach(([k, v]) => {
          if (Array.isArray(v)) {
            v.forEach((item) => searchParams.append(k, item));
          } else if (v !== undefined && v !== null && v !== '') {
            searchParams.append(k, v);
          }
        });
        return searchParams.toString();
      },
    });
    return res.data;
  },
  getCandidateReport: async (sessionId) => {
    const res = await api.get(`/auth/admin/candidates/${sessionId}/report`);
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
