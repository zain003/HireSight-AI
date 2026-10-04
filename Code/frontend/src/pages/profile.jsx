import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import resumeService from '@/services/resumeService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import { formatApiDetail } from '@/utils/formatApiDetail';
import {
  User,
  Mail,
  Briefcase,
  Sliders,
  FileText,
  Upload,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Save,
  Check,
  X,
  Clock,
  Layers,
} from 'lucide-react';

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    job_role: '',
    difficulty_level: 'medium',
    experience_years: '',
  });

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, []);

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
        // Profile may not exist yet
      }
    } catch (err) {
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const normalizeStringList = (val) => {
    if (val == null) return [];
    if (Array.isArray(val)) return val.map((s) => String(s).trim()).filter(Boolean);
    if (typeof val === 'string') {
      try {
        const p = JSON.parse(val);
        return Array.isArray(p) ? p.map((s) => String(s).trim()).filter(Boolean) : [];
      } catch {
        return [];
      }
    }
    return [];
  };

  const extractedSkills = useMemo(() => {
    if (!profile) return [];
    const base = normalizeStringList(profile.skills);
    const exp = normalizeStringList(profile.experienced_skills);
    const known = normalizeStringList(profile.known_skills);
    return Array.from(new Set([...base, ...exp, ...known]));
  }, [profile]);

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
      setMessage('Profile and interview preferences updated successfully.');
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingResume(true);
    setError('');
    setMessage('');
    try {
      const parsed = await resumeService.uploadResume(file, formData.job_role || null);
      await loadData();
      setMessage(`Resume uploaded and parsed successfully! Found ${parsed?.skills?.length || 0} skills.`);
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      console.error('Resume upload error:', err);
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to upload and parse resume.');
    } finally {
      setUploadingResume(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-2 border-indigo-600/20 border-t-indigo-600" />
          <p className="text-xs font-medium text-slate-500">Loading profile…</p>
        </div>
      </div>
    );
  }

  const initial = user?.username?.charAt(0)?.toUpperCase() || 'U';

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-800 antialiased font-sans">
      <CandidateHeader activePath="/profile" user={user} onLogout={authService.logout} />

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        onChange={handleResumeUpload}
        className="hidden"
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
        {/* Top Header Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-700 text-xl font-bold text-white shadow-xs">
                {initial}
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                  {user?.full_name || user?.username}
                </h1>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  {user?.email} · Candidate Account
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => router.push('/interview-setup')}
              className="rounded-xl bg-blue-700 hover:bg-blue-800 px-4 py-2.5 text-xs sm:text-sm font-semibold text-white transition shadow-xs"
            >
              Start Live Interview
            </button>
          </div>
        </div>

        {/* Alerts */}
        {message && (
          <div className="flex items-center justify-between rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 shadow-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>{message}</span>
            </div>
            <button onClick={() => setMessage('')} className="text-emerald-500 hover:text-emerald-700">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 shadow-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError('')} className="text-rose-500 hover:text-rose-700">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* 2-Column Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (5 cols): Account Details & Resume Status */}
          <div className="lg:col-span-5 space-y-6">
            {/* Account Info Card */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
                <User className="h-4 w-4 text-blue-700" />
                Account Details
              </h2>

              <div className="space-y-3 text-xs">
                <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Email Address</p>
                  <p className="mt-1 font-bold text-slate-900">{user?.email}</p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Username</p>
                  <p className="mt-1 font-bold text-slate-900">{user?.username}</p>
                </div>

                <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Full Name</p>
                  <p className="mt-1 font-bold text-slate-900">{user?.full_name || 'Not provided'}</p>
                </div>
              </div>
            </div>

            {/* Resume & Skills Card */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-700" />
                  Resume & Skill Cloud
                </h2>

                <button
                  type="button"
                  disabled={uploadingResume}
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                >
                  {uploadingResume ? 'Uploading…' : profile?.resume_path ? 'Replace CV' : 'Upload CV'}
                </button>
              </div>

              {profile?.resume_path ? (
                <div className="flex items-center gap-2 rounded-xl bg-emerald-50 border border-emerald-200/80 px-3 py-2 text-xs font-semibold text-emerald-800 mb-4">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Resume parsed and on file</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 rounded-xl bg-slate-50 border border-slate-200/80 px-3 py-2 text-xs font-semibold text-slate-600 mb-4">
                  <FileText className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>No resume uploaded yet</span>
                </div>
              )}

              <div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Extracted Skills ({extractedSkills.length})
                </p>
                {extractedSkills.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">
                    Upload your resume to automatically extract your technical skills.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
                    {extractedSkills.map((sk, idx) => (
                      <span
                        key={`${sk}-${idx}`}
                        className="rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-0.5 text-xs font-medium text-slate-700"
                      >
                        {sk}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column (7 cols): Interview Preferences Form */}
          <div className="lg:col-span-7 space-y-6">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
              <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
                <Sliders className="h-4 w-4 text-blue-700" />
                Interview Preferences
              </h2>
              <p className="text-xs text-slate-500 mb-6">
                These settings personalize question generation and baseline difficulty in your live interviews.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Target Job Role
                  </label>
                  <input
                    type="text"
                    name="job_role"
                    value={formData.job_role}
                    onChange={handleChange}
                    placeholder="e.g. Senior Backend Engineer, DevOps, AI Specialist"
                    className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-2xs"
                    required
                  />
                  <p className="mt-1 text-[11px] text-slate-400">
                    Questions will adapt directly to the taxonomy and competencies of this role.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Difficulty Level
                    </label>
                    <select
                      name="difficulty_level"
                      value={formData.difficulty_level}
                      onChange={handleChange}
                      className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs sm:text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-2xs"
                    >
                      <option value="easy">Junior / Entry Level (Easy)</option>
                      <option value="medium">Mid-Level (Medium)</option>
                      <option value="hard">Senior / Staff Level (Hard)</option>
                    </select>
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Years of Experience
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="50"
                      name="experience_years"
                      value={formData.experience_years}
                      onChange={handleChange}
                      placeholder="e.g. 4"
                      className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-2xs"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
                  <button
                    type="submit"
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-xl bg-blue-700 hover:bg-blue-800 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition disabled:opacity-60"
                  >
                    <Save className="h-4 w-4" />
                    {saving ? 'Saving changes…' : 'Save preferences'}
                  </button>
                </div>
              </form>
            </div>

            {/* Help & System Specs Notice */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <h3 className="text-sm font-bold text-slate-900 mb-2">Live Interview Protocol</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                When you initiate a live session, HireSight evaluates 4 objective criteria: Technical Rubric Relevance, Coding Challenge Accuracy, Speech Clarity & Pacing, and Computer Vision Head/Gaze Dynamics.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
