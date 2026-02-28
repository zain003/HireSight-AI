/**
 * Register Form Component
 */
import { useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';

export default function RegisterForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      await authService.register(registerData);
      router.push('/login?registered=true');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    'w-full px-4 py-3 bg-surface-subtle border border-deep-night/[0.08] rounded-xl text-deep-night placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-neon-violet/30 focus:border-neon-violet/40';

  return (
    <div className="p-8 bg-white rounded-2xl shadow-card border border-deep-night/[0.06] transition-shadow duration-300 hover:shadow-card-hover">
      <h2 className="text-2xl font-bold mb-1 text-center text-deep-night">Create Account</h2>
      <p className="text-text-muted text-sm text-center mb-8">Join HireSIGHT AI today</p>

      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-deep-night text-sm font-medium mb-1.5">Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="you@example.com"
            className={inputClass}
            required
          />
        </div>

        <div>
          <label className="block text-deep-night text-sm font-medium mb-1.5">Username</label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Choose a username"
            className={inputClass}
            required
          />
        </div>

        <div>
          <label className="block text-deep-night text-sm font-medium mb-1.5">Full Name</label>
          <input
            type="text"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            placeholder="Your full name"
            className={inputClass}
          />
        </div>

        <div>
          <label className="block text-deep-night text-sm font-medium mb-1.5">Password</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Min. 8 characters"
            className={inputClass}
            required
            minLength={8}
          />
        </div>

        <div>
          <label className="block text-deep-night text-sm font-medium mb-1.5">Confirm Password</label>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Repeat your password"
            className={inputClass}
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full neon-btn py-3.5 rounded-xl font-semibold text-base tracking-wide disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Creating account...
            </span>
          ) : (
            'Create Account'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-text-muted text-sm">
        Already have an account?{' '}
        <a href="/login" className="text-neon-violet font-medium hover:text-neon-glow hover:underline">
          Sign in
        </a>
      </p>
    </div>
  );
}
