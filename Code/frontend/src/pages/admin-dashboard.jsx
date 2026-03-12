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
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-deep-night/[0.06]">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <a href="/" className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-deep-night tracking-tight">
              Hire<span className="text-neon-glow">SIGHT</span>
            </h1>
            <span className="px-2 py-0.5 bg-neon-violet/10 text-neon-violet text-[10px] font-bold uppercase tracking-widest">
              Admin
            </span>
          </a>
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neon-violet to-neon-glow flex items-center justify-center">
                <span className="text-white text-xs font-bold">A</span>
              </div>
              <span className="text-deep-night text-sm font-medium hidden sm:inline">
                Admin
              </span>
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

      <main className="container mx-auto px-6 py-10 animate-fade-in">
        <div className="mb-10">
          <h2 className="text-2xl font-bold text-deep-night">
            Admin <span className="text-neon-glow">Dashboard</span>
          </h2>
          <p className="text-text-muted mt-1">
            Manage job posts and candidate matching
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm">
            {success}
          </div>
        )}

        <div className="grid sm:grid-cols-3 gap-6 mb-10">
          {[
            { label: 'Total Job Posts', value: jobPosts.length },
            {
              label: 'Active Domains',
              value: [...new Set(jobPosts.map((jp) => jp.domain).filter(Boolean))].length,
            },
            {
              label: 'Total Skills Listed',
              value: [...new Set(jobPosts.flatMap((jp) => jp.required_skills))].length,
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="border border-deep-night/[0.08] bg-white px-4 py-3 flex flex-col gap-2"
            >
              <p className="text-xl font-semibold text-deep-night">{stat.value}</p>
              <p className="text-[11px] text-text-muted uppercase tracking-wider">
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        <div className="mb-8">
          {!showCreateForm ? (
            <button
              onClick={() => {
                setShowCreateForm(true);
                setError('');
                setSuccess('');
              }}
              className="inline-flex items-center gap-2 px-6 py-2 text-sm font-semibold text-white neon-btn"
            >
              <span>＋</span>
              Create Job Post
            </button>
          ) : (
            <div className="p-6 border border-deep-night/[0.08] bg-white">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-deep-night">New Job Post</h3>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="p-2 text-text-muted hover:text-deep-night hover:bg-surface-subtle transition-colors"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreatePost} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    value={newPost.title}
                    onChange={(e) =>
                      setNewPost({ ...newPost, title: e.target.value })
                    }
                    placeholder="e.g. AI Engineer"
                    className="w-full px-3 py-2 border border-deep-night/[0.15] text-sm focus:outline-none focus:ring-1 focus:ring-neon-violet"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">
                    Description
                  </label>
                  <textarea
                    value={newPost.description}
                    onChange={(e) =>
                      setNewPost({ ...newPost, description: e.target.value })
                    }
                    placeholder="Brief job description..."
                    rows={3}
                    className="w-full px-3 py-2 border border-deep-night/[0.15] text-sm focus:outline-none focus:ring-1 focus:ring-neon-violet resize-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">
                    Required Skills *
                  </label>
                  <input
                    type="text"
                    value={newPost.required_skills}
                    onChange={(e) =>
                      setNewPost({
                        ...newPost,
                        required_skills: e.target.value,
                      })
                    }
                    placeholder="Python, Machine Learning, Deep Learning"
                    className="w-full px-3 py-2 border border-deep-night/[0.15] text-sm focus:outline-none focus:ring-1 focus:ring-neon-violet"
                    required
                  />
                  <p className="text-xs text-text-muted mt-1">
                    Separate skills with commas
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-deep-night mb-1.5">
                    Domain
                  </label>
                  <input
                    type="text"
                    value={newPost.domain}
                    onChange={(e) =>
                      setNewPost({ ...newPost, domain: e.target.value })
                    }
                    placeholder="e.g. Computing, Healthcare, Finance"
                    className="w-full px-3 py-2 border border-deep-night/[0.15] text-sm focus:outline-none focus:ring-1 focus:ring-neon-violet"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={creating}
                    className="px-6 py-2 text-sm font-semibold text-white neon-btn disabled:opacity-60"
                  >
                    {creating ? 'Creating...' : 'Create Post'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-6 py-2 text-sm font-medium text-text-muted border border-deep-night/[0.15] hover:text-deep-night hover:bg-surface-subtle"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        <div>
          <h3 className="text-lg font-bold text-deep-night mb-5">
            Job Posts
            <span className="ml-2 text-sm font-normal text-text-muted">
              ({jobPosts.length})
            </span>
          </h3>

          {jobPosts.length === 0 ? (
            <div className="p-10 bg-white border border-deep-night/[0.08] text-center">
              <div className="w-14 h-14 bg-surface-subtle border border-deep-night/20 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl text-text-muted">📄</span>
              </div>
              <p className="text-text-muted text-sm">
                No job posts yet. Create your first one!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {jobPosts.map((post) => (
                <div
                  key={post.id}
                  className="p-5 bg-white border border-deep-night/[0.08] flex flex-col gap-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-base font-bold text-deep-night">
                        {post.title}
                      </h4>
                      {post.domain && (
                        <span className="inline-block mt-1 px-2 py-0.5 border border-deep-night/20 text-[11px] text-text-muted">
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
                    <p className="text-xs text-text-muted leading-relaxed">
                      {post.description}
                    </p>
                  )}

                  {post.required_skills?.length > 0 && (
                    <div className="mt-2">
                      <p className="text-[11px] font-medium text-text-muted uppercase tracking-wider mb-2">
                        Required skills
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {post.required_skills.map((skill) => (
                          <span
                            key={skill}
                            className="px-2 py-1 text-[11px] border border-deep-night/15 bg-surface-subtle"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
