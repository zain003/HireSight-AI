/**
 * Admin Dashboard Page
 * Manages job posts, candidate skill matching, and admin operations.
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import api from '@/services/api';

export default function AdminDashboard() {
  const router = useRouter();
  const [jobPosts, setJobPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // New job post form
  const [newPost, setNewPost] = useState({
    title: '',
    description: '',
    required_skills: '',
    domain: '',
  });

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/admin-login');
      return;
    }
    loadJobPosts();
  }, [router]);

  const loadJobPosts = async () => {
    try {
      const res = await api.get('/auth/admin/job-posts');
      setJobPosts(res.data);
    } catch (err) {
      console.error('Failed to load job posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setCreating(true);
    try {
      const payload = {
        title: newPost.title.trim(),
        description: newPost.description.trim() || null,
        required_skills: newPost.required_skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        domain: newPost.domain.trim() || null,
      };
      await api.post('/auth/admin/job-post', payload);
      setSuccess('Job post created successfully!');
      setNewPost({ title: '', description: '', required_skills: '', domain: '' });
      setShowCreateForm(false);
      await loadJobPosts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create job post');
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/admin-login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-neon-violet/30 border-t-neon-violet animate-spin" />
          <p className="text-text-muted text-sm">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-deep-night/[0.06]">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <a href="/" className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-deep-night tracking-tight">
              Hire<span className="text-neon-glow">SIGHT</span>
            </h1>
            <span className="px-2 py-0.5 bg-neon-violet/10 text-neon-violet text-[10px] font-bold uppercase tracking-widest rounded-md">
              Admin
            </span>
          </a>
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neon-violet to-neon-glow flex items-center justify-center">
                <span className="text-white text-xs font-bold">A</span>
              </div>
              <span className="text-deep-night text-sm font-medium hidden sm:inline">Admin</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-text-muted border border-deep-night/[0.08] rounded-xl hover:text-deep-night hover:border-deep-night/20 hover:bg-surface-subtle transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="container mx-auto px-6 py-10 animate-fade-in">
        {/* Welcome */}
        <div className="mb-10">
          <h2 className="text-2xl font-bold text-deep-night">
            Admin <span className="text-neon-glow">Dashboard</span>
          </h2>
          <p className="text-text-muted mt-1">Manage job posts and candidate matching</p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            {error}
          </div>
        )}
        {success && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            {success}
          </div>
        )}

        {/* ── Stats Row ── */}
        <div className="grid sm:grid-cols-3 gap-6 mb-10">
          {[
            {
              label: 'Total Job Posts',
              value: jobPosts.length,
              icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
                </svg>
              ),
              color: 'from-neon-violet to-neon-glow',
            },
            {
              label: 'Active Domains',
              value: [...new Set(jobPosts.map((jp) => jp.domain).filter(Boolean))].length,
              icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
              ),
              color: 'from-blue-500 to-cyan-400',
            },
            {
              label: 'Total Skills Listed',
              value: [...new Set(jobPosts.flatMap((jp) => jp.required_skills))].length,
              icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                </svg>
              ),
              color: 'from-emerald-500 to-teal-400',
            },
          ].map((stat, i) => (
            <div key={i} className="group p-6 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card hover:shadow-card-hover transition-all duration-300">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-white`}>
                  {stat.icon}
                </div>
              </div>
              <p className="text-3xl font-bold text-deep-night">{stat.value}</p>
              <p className="text-text-muted text-sm mt-1">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* ── Create Job Post Button / Form ── */}
        <div className="mb-8">
          {!showCreateForm ? (
            <button
              onClick={() => { setShowCreateForm(true); setError(''); setSuccess(''); }}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-neon-violet to-neon-glow text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-neon-violet/25 transition-all duration-300 active:scale-[0.98]"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Create Job Post
            </button>
          ) : (
            <div className="p-6 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-deep-night">New Job Post</h3>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="p-2 text-text-muted hover:text-deep-night hover:bg-surface-subtle rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              <form onSubmit={handleCreatePost} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">Job Title *</label>
                  <input
                    type="text"
                    value={newPost.title}
                    onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                    placeholder="e.g. AI Engineer"
                    className="w-full px-4 py-2.5 border border-deep-night/[0.1] rounded-xl focus:outline-none focus:ring-2 focus:ring-neon-violet/30 focus:border-neon-violet transition-all text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">Description</label>
                  <textarea
                    value={newPost.description}
                    onChange={(e) => setNewPost({ ...newPost, description: e.target.value })}
                    placeholder="Brief job description..."
                    rows={3}
                    className="w-full px-4 py-2.5 border border-deep-night/[0.1] rounded-xl focus:outline-none focus:ring-2 focus:ring-neon-violet/30 focus:border-neon-violet transition-all text-sm resize-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">Required Skills *</label>
                  <input
                    type="text"
                    value={newPost.required_skills}
                    onChange={(e) => setNewPost({ ...newPost, required_skills: e.target.value })}
                    placeholder="Python, Machine Learning, Deep Learning (comma-separated)"
                    className="w-full px-4 py-2.5 border border-deep-night/[0.1] rounded-xl focus:outline-none focus:ring-2 focus:ring-neon-violet/30 focus:border-neon-violet transition-all text-sm"
                    required
                  />
                  <p className="text-xs text-text-muted mt-1">Separate skills with commas</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">Domain</label>
                  <input
                    type="text"
                    value={newPost.domain}
                    onChange={(e) => setNewPost({ ...newPost, domain: e.target.value })}
                    placeholder="e.g. Computing, Healthcare, Finance"
                    className="w-full px-4 py-2.5 border border-deep-night/[0.1] rounded-xl focus:outline-none focus:ring-2 focus:ring-neon-violet/30 focus:border-neon-violet transition-all text-sm"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={creating}
                    className="px-6 py-2.5 bg-gradient-to-r from-neon-violet to-neon-glow text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-neon-violet/25 transition-all duration-300 disabled:opacity-60 text-sm"
                  >
                    {creating ? 'Creating...' : 'Create Post'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-6 py-2.5 text-sm font-medium text-text-muted border border-deep-night/[0.08] rounded-xl hover:text-deep-night hover:bg-surface-subtle transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* ── Job Posts List ── */}
        <div>
          <h3 className="text-lg font-bold text-deep-night mb-5">
            Job Posts
            <span className="ml-2 text-sm font-normal text-text-muted">({jobPosts.length})</span>
          </h3>

          {jobPosts.length === 0 ? (
            <div className="p-12 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-subtle flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" />
                </svg>
              </div>
              <p className="text-text-muted text-sm">No job posts yet. Create your first one!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {jobPosts.map((post) => (
                <div
                  key={post.id}
                  className="p-6 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card hover:shadow-card-hover transition-all duration-300 relative overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-neon-violet to-neon-glow rounded-r" />
                  <div className="pl-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="text-base font-bold text-deep-night">{post.title}</h4>
                        {post.domain && (
                          <span className="inline-block mt-1 px-2.5 py-0.5 bg-neon-violet/10 text-neon-violet text-xs font-medium rounded-md">
                            {post.domain}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-text-muted whitespace-nowrap">
                        {new Date(post.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </div>

                    {post.description && (
                      <p className="text-sm text-text-muted mb-3 leading-relaxed">{post.description}</p>
                    )}

                    {post.required_skills?.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Required Skills</p>
                        <div className="flex flex-wrap gap-1.5">
                          {post.required_skills.map((skill, i) => (
                            <span
                              key={i}
                              className="px-2.5 py-1 bg-deep-night/[0.05] text-deep-night rounded-lg text-xs font-medium"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
