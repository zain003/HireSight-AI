/**
 * Admin Dashboard Page
 * Manages job posts, candidate skill matching, and admin operations.
 */
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import api from '@/services/api';
import adminDashboardService from '@/services/adminDashboardService';
import { formatApiDetail } from '@/utils/formatApiDetail';
import {
  LayoutDashboard,
  Users,
  Settings,
  Briefcase,
  Search,
  Bell,
  Plus,
  Eye,
  Pencil,
  Trash2,
  Video,
  Code2,
} from 'lucide-react';

function normalizeRequiredSkills(raw) {
  return (raw || '')
    .replace(/([a-z])([A-Z])/g, '$1, $2')
    .split(/[,;\n/]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function postStatus(post) {
  const s = (post.status || 'active').toLowerCase();
  if (s === 'active' || s === 'draft' || s === 'closed') return s;
  return 'active';
}

const JOB_STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'draft', label: 'Draft' },
  { value: 'closed', label: 'Closed' },
];

export default function AdminDashboard() {
  const router = useRouter();
  const [activeSection, setActiveSection] = useState('dashboard');
  const [jobPosts, setJobPosts] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const [viewJob, setViewJob] = useState(null);
  const [editJob, setEditJob] = useState(null);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    required_skills: '',
    domain: '',
    status: 'active',
  });
  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const [newPost, setNewPost] = useState({
    title: '',
    description: '',
    required_skills: '',
    domain: '',
    status: 'active',
  });

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/admin-login');
      return;
    }
    loadAllData();
  }, [router]);

  const loadJobPosts = async () => {
    const res = await api.get('/auth/admin/job-posts');
    setJobPosts(res.data);
  };

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [postsRes, statsRes, usersRes] = await Promise.allSettled([
        api.get('/auth/admin/job-posts'),
        adminDashboardService.getStats(),
        adminDashboardService.getUsers(),
      ]);
      if (postsRes.status === 'fulfilled') setJobPosts(postsRes.value.data);
      if (statsRes.status === 'fulfilled') setDashboardStats(statsRes.value);
      if (usersRes.status === 'fulfilled') setUsers(usersRes.value);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPosts = useMemo(() => {
    let list = jobPosts;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (p) =>
          p.title?.toLowerCase().includes(q) ||
          (p.description || '').toLowerCase().includes(q) ||
          (p.domain || '').toLowerCase().includes(q) ||
          (p.required_skills || []).some((s) => s.toLowerCase().includes(q))
      );
    }
    if (statusFilter === 'active') {
      list = list.filter((p) => postStatus(p) === 'active');
    } else if (statusFilter === 'draft') {
      list = list.filter((p) => postStatus(p) === 'draft');
    } else if (statusFilter === 'closed') {
      list = list.filter((p) => postStatus(p) === 'closed');
    }
    return list;
  }, [jobPosts, searchQuery, statusFilter]);

  const filteredUsers = useMemo(() => {
    if (!userSearch.trim()) return users;
    const q = userSearch.toLowerCase();
    return users.filter(
      (u) =>
        u.email?.toLowerCase().includes(q) ||
        u.username?.toLowerCase().includes(q) ||
        (u.full_name || '').toLowerCase().includes(q) ||
        (u.job_role || '').toLowerCase().includes(q)
    );
  }, [users, userSearch]);

  const openEdit = (post) => {
    setEditJob(post);
    setEditForm({
      title: post.title || '',
      description: post.description || '',
      required_skills: Array.isArray(post.required_skills)
        ? post.required_skills.join(', ')
        : '',
      domain: post.domain || '',
      status: postStatus(post),
    });
    setError('');
    setSuccess('');
  };

  const handleUpdatePost = async (e) => {
    e.preventDefault();
    if (!editJob?.id) return;
    setError('');
    setSuccess('');
    setSavingEdit(true);
    try {
      const payload = {
        title: editForm.title.trim(),
        description: editForm.description.trim() || null,
        required_skills: normalizeRequiredSkills(editForm.required_skills),
        domain: editForm.domain.trim() || null,
        status: editForm.status,
      };
      await api.put(`/auth/admin/job-posts/${editJob.id}`, payload);
      setSuccess('Job post updated successfully.');
      setEditJob(null);
      await loadJobPosts();
      try {
        setDashboardStats(await adminDashboardService.getStats());
      } catch {
        /* ignore */
      }
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to update job post');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeletePost = async (post) => {
    if (
      !window.confirm(
        `Delete "${post.title}"? Candidates can no longer apply to this job.`
      )
    ) {
      return;
    }
    setError('');
    setSuccess('');
    setDeletingId(post.id);
    try {
      await api.delete(`/auth/admin/job-posts/${post.id}`);
      setSuccess('Job post deleted.');
      setViewJob(null);
      if (editJob?.id === post.id) setEditJob(null);
      await loadJobPosts();
      try {
        setDashboardStats(await adminDashboardService.getStats());
      } catch {
        /* ignore */
      }
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to delete job post');
    } finally {
      setDeletingId(null);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setCreating(true);
    try {
      const normalizedRequiredSkills = normalizeRequiredSkills(
        newPost.required_skills
      );

      const payload = {
        title: newPost.title.trim(),
        description: newPost.description.trim() || null,
        required_skills: normalizedRequiredSkills,
        domain: newPost.domain.trim() || null,
        status: newPost.status,
      };
      await api.post('/auth/admin/job-post', payload);
      setSuccess('Job post created successfully!');
      setNewPost({
        title: '',
        description: '',
        required_skills: '',
        domain: '',
        status: 'active',
      });
      setShowCreateForm(false);
      await loadJobPosts();
      try {
        setDashboardStats(await adminDashboardService.getStats());
      } catch {
        /* ignore */
      }
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to create job post');
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/admin-login');
  };

  const statusPill = (status) => {
    const styles = {
      active: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      draft: 'bg-slate-600/40 text-slate-300 border-slate-500/30',
      closed: 'bg-red-500/15 text-red-300 border-red-500/30',
    };
    const labels = { active: 'Active', draft: 'Draft', closed: 'Closed' };
    return (
      <span
        className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status] || styles.draft}`}
      >
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0B1120]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-400/30 border-t-indigo-400" />
          <p className="text-sm text-slate-400">Loading admin dashboard…</p>
        </div>
      </div>
    );
  }

  const navItem = (sectionId, Icon, label) => (
    <button
      type="button"
      title={label}
      onClick={() => {
        setActiveSection(sectionId);
        if (sectionId !== 'dashboard' && sectionId !== 'jobs') {
          setShowCreateForm(false);
        }
      }}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${
        activeSection === sectionId
          ? 'bg-indigo-500/20 text-indigo-200'
          : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
      }`}
    >
      <Icon className="h-5 w-5 shrink-0 opacity-90" strokeWidth={1.75} />
      <span className="hidden font-medium lg:inline">{label}</span>
    </button>
  );

  const sectionMeta = {
    dashboard: {
      title: 'Admin Dashboard',
      subtitle: 'Manage job posts, candidates, and interview sessions',
    },
    users: {
      title: 'Users',
      subtitle: 'Registered accounts and profile summary',
    },
    jobs: {
      title: 'Job posts',
      subtitle: 'Create and manage listings',
    },
    settings: {
      title: 'Settings',
      subtitle: 'Environment and your admin session',
    },
  };
  const { title: pageTitle, subtitle: pageSubtitle } =
    sectionMeta[activeSection] || sectionMeta.dashboard;

  const s = dashboardStats || {};
  const statCards = [
    {
      label: 'Total job posts',
      value: s.total_job_posts ?? '—',
      icon: Briefcase,
      trend: `+${s.job_posts_created_this_week ?? 0} this week`,
      iconBg: 'bg-indigo-500/20 text-indigo-300',
    },
    {
      label: 'Registered users',
      value: s.total_registered_users ?? '—',
      icon: Users,
      trend: `+${s.users_registered_this_week ?? 0} this week`,
      iconBg: 'bg-sky-500/20 text-sky-300',
    },
    {
      label: 'Interviews today',
      value: s.interviews_today ?? '—',
      icon: Video,
      trend: `${s.interviews_this_week ?? 0} in last 7 days`,
      iconBg: 'bg-violet-500/20 text-violet-300',
    },
    {
      label: 'Profiles with resume',
      value: s.profiles_with_resume ?? '—',
      icon: Code2,
      trend: `${s.unique_skills_listed ?? 0} unique skills in job posts`,
      iconBg: 'bg-amber-500/20 text-amber-200',
    },
  ];

  return (
    <div className="flex min-h-screen bg-[#0B1120] text-slate-100">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 flex w-[72px] flex-col border-r border-white/10 bg-[#0d1526] lg:w-56">
        <div className="flex h-16 items-center justify-center border-b border-white/10 lg:justify-start lg:px-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 text-lg font-bold text-white">
            H
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2">
          {navItem('dashboard', LayoutDashboard, 'Dashboard')}
          {navItem('users', Users, 'Users')}
          {navItem('jobs', Briefcase, 'Jobs')}
          {navItem('settings', Settings, 'Settings')}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col pl-[72px] lg:pl-56">
        {/* Top bar */}
        <header className="sticky top-0 z-20 border-b border-white/10 bg-[#0B1120]/90 backdrop-blur-md">
          <div className="flex flex-col gap-4 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <a href="/" className="shrink-0 text-lg font-bold tracking-tight text-white">
                Hire<span className="text-indigo-400">SIGHT</span>
              </a>
              <span className="rounded-md border border-indigo-400/40 bg-indigo-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-indigo-200">
                Admin
              </span>
            </div>

            {activeSection === 'settings' ? (
              <div className="hidden flex-1 sm:block sm:px-6" aria-hidden />
            ) : (
              <div className="relative mx-auto w-full max-w-xl sm:mx-0 sm:flex-1 sm:px-6">
                <Search
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
                  strokeWidth={1.75}
                />
                <input
                  type="search"
                  value={activeSection === 'users' ? userSearch : searchQuery}
                  onChange={(e) =>
                    activeSection === 'users'
                      ? setUserSearch(e.target.value)
                      : setSearchQuery(e.target.value)
                  }
                  placeholder={
                    activeSection === 'users'
                      ? 'Search users by email, name…'
                      : 'Search jobs, skills, domain…'
                  }
                  className="w-full rounded-xl border border-white/10 bg-slate-900/80 py-2.5 pl-10 pr-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                />
              </div>
            )}

            <div className="flex items-center justify-end gap-2 sm:gap-3">
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-full text-slate-400 transition hover:bg-white/5 hover:text-white"
                aria-label="Notifications"
              >
                <Bell className="h-5 w-5" strokeWidth={1.75} />
              </button>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">
                A
              </div>
              <span className="hidden text-sm font-medium text-slate-300 sm:inline">Admin</span>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-xl border border-white/15 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-white/5 hover:text-white"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 space-y-8 px-4 py-8 sm:px-6">
          {/* Page header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white sm:text-3xl">{pageTitle}</h1>
              <p className="mt-1 text-sm text-slate-400">{pageSubtitle}</p>
            </div>
            {(activeSection === 'dashboard' || activeSection === 'jobs') && !showCreateForm && (
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(true);
                  setError('');
                  setSuccess('');
                }}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-600"
              >
                <Plus className="h-5 w-5" strokeWidth={2} />
                Create Job Post
              </button>
            )}
          </div>

          {error && (
            <div className="rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              {success}
            </div>
          )}

          {/* Stats (API) */}
          {activeSection === 'dashboard' && (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {statCards.map((card) => (
                <div
                  key={card.label}
                  className="rounded-2xl border border-white/10 bg-slate-900/50 p-5 transition hover:border-white/15"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl ${card.iconBg}`}
                    >
                      <card.icon className="h-5 w-5" strokeWidth={1.75} />
                    </div>
                    <span className="max-w-[52%] text-right rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                      {card.trend}
                    </span>
                  </div>
                  <p className="mt-4 text-3xl font-bold text-white">{card.value}</p>
                  <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                    {card.label}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Create form */}
          {(activeSection === 'dashboard' || activeSection === 'jobs') && showCreateForm && (
            <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-6">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">New Job Post</h2>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white"
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreatePost} className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                    Job title *
                  </label>
                  <input
                    type="text"
                    value={newPost.title}
                    onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                    placeholder="e.g. Java Developer"
                    className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                    required
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                    Description
                  </label>
                  <textarea
                    value={newPost.description}
                    onChange={(e) =>
                      setNewPost({ ...newPost, description: e.target.value })
                    }
                    placeholder="Brief job description…"
                    rows={3}
                    className="w-full resize-none rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                    Required skills *
                  </label>
                  <input
                    type="text"
                    value={newPost.required_skills}
                    onChange={(e) =>
                      setNewPost({ ...newPost, required_skills: e.target.value })
                    }
                    placeholder="Python, Docker, PostgreSQL"
                    className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                    required
                  />
                  <p className="mt-1 text-xs text-slate-500">Separate skills with commas</p>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                    Status
                  </label>
                  <select
                    value={newPost.status}
                    onChange={(e) => setNewPost({ ...newPost, status: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                  >
                    {JOB_STATUS_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                    Domain
                  </label>
                  <input
                    type="text"
                    value={newPost.domain}
                    onChange={(e) => setNewPost({ ...newPost, domain: e.target.value })}
                    placeholder="e.g. Computing"
                    className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                  />
                </div>
                <div className="flex flex-wrap gap-3 sm:col-span-2">
                  <button
                    type="submit"
                    disabled={creating}
                    className="rounded-xl bg-indigo-500 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-600 disabled:opacity-50"
                  >
                    {creating ? 'Creating…' : 'Create Post'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="rounded-xl border border-white/15 px-6 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/5"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Users */}
          {activeSection === 'users' && (
            <section className="rounded-2xl border border-white/10 bg-slate-900/40">
              <div className="flex flex-col gap-4 border-b border-white/10 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-white">All users</h2>
                  <span className="rounded-full border border-indigo-400/40 bg-indigo-500/15 px-2.5 py-0.5 text-xs font-semibold text-indigo-200">
                    {users.length}
                  </span>
                </div>
              </div>
              {users.length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <Users className="mx-auto mb-3 h-12 w-12 opacity-40" strokeWidth={1} />
                  <p className="text-sm">No users found.</p>
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <p className="text-sm">No users match your search.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[880px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-white/10 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        <th className="px-5 py-4">Email</th>
                        <th className="px-5 py-4">Name</th>
                        <th className="px-5 py-4">Username</th>
                        <th className="px-5 py-4">Joined</th>
                        <th className="px-5 py-4">Resume</th>
                        <th className="px-5 py-4">Role / skills</th>
                        <th className="px-5 py-4">Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((u) => (
                        <tr
                          key={u.id}
                          className="border-b border-white/5 transition hover:bg-white/[0.03]"
                        >
                          <td className="px-5 py-4 align-top text-slate-200">{u.email}</td>
                          <td className="px-5 py-4 align-top text-slate-300">
                            {u.full_name || '—'}
                          </td>
                          <td className="px-5 py-4 align-top text-slate-400">
                            {u.username || '—'}
                          </td>
                          <td className="px-5 py-4 align-top text-slate-400">
                            {u.created_at
                              ? new Date(u.created_at).toLocaleDateString('en-US', {
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric',
                                })
                              : '—'}
                          </td>
                          <td className="px-5 py-4 align-top">
                            {u.has_resume ? (
                              <span className="text-emerald-300">Yes</span>
                            ) : (
                              <span className="text-slate-500">No</span>
                            )}
                          </td>
                          <td className="px-5 py-4 align-top text-slate-400">
                            <span className="text-slate-300">{u.job_role || '—'}</span>
                            <span className="mt-1 block text-[11px] text-slate-500">
                              {u.skills_count != null ? `${u.skills_count} skills` : ''}
                            </span>
                          </td>
                          <td className="px-5 py-4 align-top">
                            {u.is_active !== false ? (
                              <span className="text-emerald-300">Yes</span>
                            ) : (
                              <span className="text-amber-300">No</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {/* Settings */}
          {activeSection === 'settings' && (
            <div className="space-y-6 rounded-2xl border border-white/10 bg-slate-900/40 p-6">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  API base URL
                </p>
                <p className="mt-1 font-mono text-sm text-slate-200">
                  {process.env.NEXT_PUBLIC_API_URL ||
                    'Same origin (relative /api or configured proxy)'}
                </p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Session
                </p>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="mt-2 rounded-xl border border-white/15 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-white/5"
                >
                  Log out of admin
                </button>
              </div>
            </div>
          )}

          {/* Job posts table */}
          {(activeSection === 'dashboard' || activeSection === 'jobs') && (
          <section className="rounded-2xl border border-white/10 bg-slate-900/40">
            <div className="flex flex-col gap-4 border-b border-white/10 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">Job posts</h2>
                <span className="rounded-full border border-indigo-400/40 bg-indigo-500/15 px-2.5 py-0.5 text-xs font-semibold text-indigo-200">
                  {jobPosts.length}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'active', label: 'Active' },
                  { id: 'draft', label: 'Draft' },
                  { id: 'closed', label: 'Closed' },
                ].map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => setStatusFilter(f.id)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      statusFilter === f.id
                        ? 'bg-white/10 text-white'
                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {jobPosts.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <Briefcase className="mx-auto mb-3 h-12 w-12 opacity-40" strokeWidth={1} />
                <p className="text-sm">No job posts yet. Create your first one.</p>
              </div>
            ) : filteredPosts.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <p className="text-sm">
                  {statusFilter === 'closed'
                    ? 'No closed job posts yet.'
                    : 'No jobs match this filter or search.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      <th className="px-5 py-4">Job title</th>
                      <th className="px-5 py-4">Date posted</th>
                      <th className="px-5 py-4">Status</th>
                      <th className="px-5 py-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPosts.map((post) => {
                      const st = postStatus(post);
                      const sub =
                        (post.description || '').trim().slice(0, 80) ||
                        (post.domain ? `${post.domain} role` : 'Role listing');
                      return (
                        <tr
                          key={post.id}
                          className="border-b border-white/5 transition hover:bg-white/[0.03]"
                        >
                          <td className="px-5 py-4 align-top">
                            <p className="font-semibold text-white">{post.title}</p>
                            <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{sub}</p>
                            {post.domain && (
                              <span className="mt-2 inline-block rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-400">
                                {post.domain}
                              </span>
                            )}
                          </td>
                          <td className="px-5 py-4 align-top text-slate-400">
                            {new Date(post.created_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })}
                          </td>
                          <td className="px-5 py-4 align-top">{statusPill(st)}</td>
                          <td className="px-5 py-4 align-top">
                            <div className="flex flex-wrap items-center justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => {
                                  setViewJob(post);
                                  setError('');
                                }}
                                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-600"
                              >
                                <Eye className="h-3.5 w-3.5" strokeWidth={2} />
                                View
                              </button>
                              <button
                                type="button"
                                onClick={() => openEdit(post)}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:bg-white/5"
                              >
                                <Pencil className="h-3.5 w-3.5" strokeWidth={2} />
                                Edit
                              </button>
                              <button
                                type="button"
                                disabled={deletingId === post.id}
                                onClick={() => handleDeletePost(post)}
                                className="inline-flex items-center justify-center rounded-lg border border-red-400/30 p-1.5 text-red-300 transition hover:bg-red-500/10 disabled:opacity-50"
                                aria-label="Delete"
                              >
                                <Trash2 className="h-4 w-4" strokeWidth={2} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          )}
        </main>
      </div>

      {/* View job modal */}
      {viewJob && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="view-job-title"
        >
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#0d1526] p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h3 id="view-job-title" className="text-lg font-bold text-white">
                  {viewJob.title}
                </h3>
                {viewJob.domain && (
                  <span className="mt-2 inline-block rounded-md border border-white/10 px-2 py-0.5 text-[11px] text-slate-400">
                    {viewJob.domain}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setViewJob(null)}
                className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div className="mb-4 flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <span>
                Created{' '}
                {new Date(viewJob.created_at).toLocaleString(undefined, {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                })}
              </span>
              {statusPill(postStatus(viewJob))}
            </div>
            {viewJob.description ? (
              <div className="mb-4">
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Description
                </p>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                  {viewJob.description}
                </p>
              </div>
            ) : (
              <p className="mb-4 text-sm italic text-slate-500">No description provided.</p>
            )}
            {viewJob.required_skills?.length > 0 && (
              <div>
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Required skills
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {viewJob.required_skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-slate-300"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-6 flex flex-wrap gap-2 border-t border-white/10 pt-4">
              <button
                type="button"
                onClick={() => {
                  openEdit(viewJob);
                  setViewJob(null);
                }}
                className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-600"
              >
                Edit this job
              </button>
              <button
                type="button"
                onClick={() => setViewJob(null)}
                className="rounded-xl border border-white/15 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/5"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit job modal */}
      {editJob && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-job-title"
        >
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#0d1526] p-6 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <h3 id="edit-job-title" className="text-lg font-bold text-white">
                Edit job post
              </h3>
              <button
                type="button"
                onClick={() => setEditJob(null)}
                className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleUpdatePost} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                  Job title *
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                  Description
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                  rows={4}
                  className="w-full resize-none rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                  Required skills *
                </label>
                <input
                  type="text"
                  value={editForm.required_skills}
                  onChange={(e) =>
                    setEditForm({ ...editForm, required_skills: e.target.value })
                  }
                  placeholder="Python, Docker, AWS"
                  className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                  required
                />
                <p className="mt-1 text-xs text-slate-500">Separate skills with commas</p>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                  Status
                </label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                >
                  {JOB_STATUS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                  Domain
                </label>
                <input
                  type="text"
                  value={editForm.domain}
                  onChange={(e) => setEditForm({ ...editForm, domain: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-[#0B1120] px-4 py-2.5 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                />
              </div>
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="rounded-xl bg-indigo-500 px-6 py-2.5 text-sm font-semibold text-white hover:bg-indigo-600 disabled:opacity-50"
                >
                  {savingEdit ? 'Saving…' : 'Save changes'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditJob(null)}
                  className="rounded-xl border border-white/15 px-6 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/5"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
