/**
 * Authentication API service
 */
import api from './api';

export const authService = {
  /**
   * Register a new user
   */
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  /**
   * Login user
   */
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return response.data;
  },

  /**
   * Admin login
   */
  adminLogin: async (credentials) => {
    const response = await api.post('/auth/admin/login', credentials);
    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return response.data;
  },

  /**
   * Logout user
   */
  logout: () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  },

  /**
   * Get current user info
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Get user profile
   */
  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (profileData) => {
    const response = await api.post('/auth/profile', profileData);
    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get raw access token
   */
  getAccessToken: () => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  /**
   * Decode JWT payload safely
   */
  getDecodedToken: () => {
    if (typeof window === 'undefined') return null;
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return null;
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      const payload = JSON.parse(atob(parts[1]));
      return payload;
    } catch {
      return null;
    }
  },

  /**
   * Check if the authenticated user has admin role
   */
  isAdminAuthenticated: () => {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem('access_token');
    if (!token) return false;
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return false;
      const payload = JSON.parse(atob(parts[1]));
      return payload?.username === 'admin' || payload?.user_id === 'admin' || payload?.role === 'admin';
    } catch {
      return false;
    }
  },

  /**
   * Logout admin and redirect to admin login
   */
  adminLogout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      window.location.href = '/admin-login';
    }
  },
};

export default authService;
