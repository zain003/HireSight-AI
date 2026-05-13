import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import { formatApiDetail } from '@/utils/formatApiDetail';

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    job_role: '',
    difficulty_level: 'medium',
    experience_years: '',
  });

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
      try {
        const profileData = await authService.getProfile();
        setProfile(profileData);
        setFormData({
          job_role: profileData.job_role || '',
          difficulty_level: profileData.difficulty_level || 'medium',
          experience_years: profileData.experience_years ?? '',
        });
      } catch (err) {
        // Profile may not exist yet; keep defaults
      }
    } catch (err) {
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setMessage('');
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const payload = {
        job_role: formData.job_role.trim(),
        difficulty_level: formData.difficulty_level,
        experience_years:
          formData.experience_years === '' ? null : Number(formData.experience_years),
      };
      const updated = await authService.updateProfile(payload);
      setProfile(updated);
      setMessage('Profile updated successfully.');
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-300">Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      <CandidateHeader activePath="/profile" user={user} onLogout={authService.logout} />
      <main className="container mx-auto space-y-6 px-6 py-8">
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-white">Profile</h1>
          <p className="mt-1 text-sm text-slate-300">Review your account details and update interview preferences.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-white">Account details</h2>
            <div className="mt-4 space-y-3 text-sm">
              <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
                <p className="text-xs uppercase tracking-[0.12em] text-slate-400">Email</p>
                <p className="mt-1 font-medium text-white">{user?.email}</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
                <p className="text-xs uppercase tracking-[0.12em] text-slate-400">Username</p>
                <p className="mt-1 font-medium text-white">{user?.username}</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
                <p className="text-xs uppercase tracking-[0.12em] text-slate-400">Full name</p>
                <p className="mt-1 font-medium text-white">{user?.full_name || 'Not set'}</p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-white">Interview preferences</h2>

            {message && (
              <div className="mt-4 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
                {message}
              </div>
            )}
            {error && (
              <div className="mt-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-300">Target job role</label>
                <input
                  type="text"
                  name="job_role"
                  value={formData.job_role}
                  onChange={handleChange}
                  placeholder="e.g. AI Engineer"
                  className="w-full rounded-lg border border-white/15 bg-slate-950/50 px-3 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  required
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-300">Difficulty level</label>
                <select
                  name="difficulty_level"
                  value={formData.difficulty_level}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-white/15 bg-slate-950/50 px-3 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-300">Experience years</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  name="experience_years"
                  value={formData.experience_years}
                  onChange={handleChange}
                  placeholder="0"
                  className="w-full rounded-lg border border-white/15 bg-slate-950/50 px-3 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {saving ? 'Saving...' : 'Save preferences'}
              </button>
            </form>

            {profile?.resume_path && (
              <p className="mt-4 text-xs text-slate-400">
                Resume is already uploaded and linked to your profile.
              </p>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
