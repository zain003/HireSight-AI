/**
 * Admin Dashboard Page
 * Manages job posts, candidate skill matching, and admin operations.
 * Features ultra-clean, executive White & Professional Theme with instant Dark Mode toggle.
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
  UserCheck,
  Sun,
  Moon,
  ArrowLeft,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import JobCandidatesList from '@/components/Admin/JobCandidatesList';
import CandidateAssessmentRoster from '@/components/Admin/CandidateAssessmentRoster';
import RecruiterReportViewer from '@/components/Interview/RecruiterReportViewer';

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
  const [theme, setTheme] = useState('light');
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

  // States for candidate viewing
  const [viewMode, setViewMode] = useState('list'); // 'list', 'candidates', 'report'
  const [selectedJobForCandidates, setSelectedJobForCandidates] = useState(null);
  const [selectedSessionForReport, setSelectedSessionForReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

  const [newPost, setNewPost] = useState({
    title: '',
    description: '',
    required_skills: '',
    domain: '',
    status: 'active',
  });

  useEffect(() => {
    const savedTheme = localStorage.getItem('hiresight_admin_theme') || 'light';
    setTheme(savedTheme);
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    localStorage.setItem('hiresight_admin_theme', nextTheme);
  };

  const isLight = theme === 'light';

  useEffect(() => {
    if (!authService.isAuthenticated() || !authService.isAdminAuthenticated()) {
      router.push('/admin-login');
      return;
    }
    loadAllData();
  }, []);

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

  const handleViewCandidates = (job) => {
    setSelectedJobForCandidates(job);
    setViewMode('candidates');
    setError('');
    setSuccess('');
  };

  const handleViewReport = async (sessionId) => {
    try {
      setLoadingReport(true);
      setError('');
      const response = await adminDashboardService.getCandidateReport(sessionId);
      setReportData(response);
      setSelectedSessionForReport(sessionId);
      setViewMode('report');
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to load candidate assessment report');
    } finally {
      setLoadingReport(false);
    }
  };

  const handleBackFromCandidates = () => {
    setViewMode('list');
    setSelectedJobForCandidates(null);
  };

  const handleBackFromReport = () => {
    if (selectedJobForCandidates) {
      setViewMode('candidates');
    } else {
      setViewMode('list');
    }
    setReportData(null);
    setSelectedSessionForReport(null);
  };

  const statusPill = (status) => {
    const stylesLight = {
      active: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      draft: 'bg-slate-100 text-slate-600 border-slate-200',
      closed: 'bg-rose-50 text-rose-700 border-rose-200',
    };
    const stylesDark = {
      active: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      draft: 'bg-slate-600/40 text-slate-300 border-slate-500/30',
      closed: 'bg-red-500/15 text-red-300 border-red-500/30',
    };
    const currentStyles = isLight ? stylesLight : stylesDark;
    const labels = { active: 'Active', draft: 'Draft', closed: 'Closed' };
    return (
      <span
        className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold ${currentStyles[status] || currentStyles.draft}`}
      >
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className={`flex min-h-screen items-center justify-center ${isLight ? 'bg-[#F8FAFC]' : 'bg-[#0B1120]'}`}>
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          <p className={`text-sm font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Loading admin dashboard…</p>
        </div>
      </div>
    );
  }

  const navItem = (sectionId, Icon, label) => {
    const isActive = activeSection === sectionId;
    const activeClass = isLight
      ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-xs'
      : 'bg-indigo-500/20 text-indigo-200 font-semibold';
    const inactiveClass = isLight
      ? 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 font-medium'
      : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 font-medium';

    return (
      <button
        type="button"
        title={label}
        onClick={() => {
          setActiveSection(sectionId);
          setViewMode('list');
          setSelectedJobForCandidates(null);
          setReportData(null);
          if (sectionId !== 'dashboard' && sectionId !== 'jobs') {
            setShowCreateForm(false);
          }
        }}
        className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-sm transition ${
          isActive ? activeClass : inactiveClass
        }`}
      >
        <Icon className="h-5 w-5 shrink-0 opacity-90" strokeWidth={1.75} />
        <span className="hidden lg:inline">{label}</span>
      </button>
    );
  };

  const sectionMeta = {
    dashboard: {
      title: viewMode === 'candidates' 
        ? `Candidates - ${selectedJobForCandidates?.title || ''}`
        : viewMode === 'report'
        ? 'Candidate Assessment Dossier'
        : 'Admin Dashboard',
      subtitle: viewMode === 'candidates'
        ? 'Review candidates who completed interviews for this job'
        : viewMode === 'report'
        ? 'Comprehensive hiring decision report & 5-dimensional scores'
        : 'Manage job postings, candidate evaluations, and recruitment analytics',
    },
    candidates: {
      title: viewMode === 'report'
        ? 'Candidate Assessment Dossier'
        : 'Candidate Assessments',
      subtitle: viewMode === 'report'
        ? 'Comprehensive hiring decision report & 5-dimensional scores'
        : 'Search, filter, and inspect candidate interview performance',
    },
    users: {
      title: 'Users',
      subtitle: 'Registered accounts and candidate profile summary',
    },
    jobs: {
      title: viewMode === 'candidates'
        ? `Candidates - ${selectedJobForCandidates?.title || ''}`
        : viewMode === 'report'
        ? 'Candidate Assessment Dossier'
        : 'Job Posts',
      subtitle: viewMode === 'candidates'
        ? 'Review candidates who completed interviews for this job'
        : viewMode === 'report'
        ? 'Comprehensive hiring decision report & 5-dimensional scores'
        : 'Create, update, and manage company job listings',
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
      iconBg: isLight ? 'bg-indigo-50 text-indigo-600 border border-indigo-100' : 'bg-indigo-500/20 text-indigo-300',
    },
    {
      label: 'Registered users',
      value: s.total_registered_users ?? '—',
      icon: Users,
      trend: `+${s.users_registered_this_week ?? 0} this week`,
      iconBg: isLight ? 'bg-sky-50 text-sky-600 border border-sky-100' : 'bg-sky-500/20 text-sky-300',
    },
    {
      label: 'Interviews today',
      value: s.interviews_today ?? '—',
      icon: Video,
      trend: `${s.interviews_this_week ?? 0} in last 7 days`,
      iconBg: isLight ? 'bg-violet-50 text-violet-600 border border-violet-100' : 'bg-violet-500/20 text-violet-300',
    },
    {
      label: 'Profiles with resume',
      value: s.profiles_with_resume ?? '—',
      icon: Code2,
      trend: `${s.unique_skills_listed ?? 0} unique skills`,
      iconBg: isLight ? 'bg-amber-50 text-amber-600 border border-amber-100' : 'bg-amber-500/20 text-amber-200',
    },
  ];

  return (
    <div className={`flex min-h-screen transition-colors duration-200 ${isLight ? 'bg-[#F8FAFC] text-slate-900' : 'bg-[#0B1120] text-slate-100'}`}>
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-[72px] flex-col border-r transition-colors duration-200 lg:w-56 ${
        isLight ? 'bg-white border-slate-200 shadow-xs' : 'bg-[#0d1526] border-white/10'
      }`}>
        <div className={`flex h-16 items-center justify-center border-b lg:justify-start lg:px-4 ${
          isLight ? 'border-slate-100' : 'border-white/10'
        }`}>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-lg font-bold text-white shadow-md shadow-indigo-500/20">
            H
          </div>
          <div className="hidden lg:block ml-3">
            <span className={`text-base font-extrabold tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
              Hire<span className="text-indigo-600">SIGHT</span>
            </span>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2">
          {navItem('dashboard', LayoutDashboard, 'Dashboard')}
          {navItem('candidates', UserCheck, 'Candidates')}
          {navItem('jobs', Briefcase, 'Jobs')}
          {navItem('users', Users, 'Users')}
          {navItem('settings', Settings, 'Settings')}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col pl-[72px] lg:pl-56">
        {/* Top bar */}
        <header className={`sticky top-0 z-20 border-b backdrop-blur-md transition-colors duration-200 ${
          isLight ? 'border-slate-200/80 bg-white/95 shadow-xs' : 'border-white/10 bg-[#0B1120]/90'
        }`}>
          <div className="flex flex-col gap-4 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <a href="/" className={`shrink-0 text-lg font-bold tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
                Hire<span className="text-indigo-600">SIGHT</span>
              </a>
              <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                isLight ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-indigo-400/40 bg-indigo-500/15 text-indigo-200'
              }`}>
                Admin Portal
              </span>
            </div>

            {activeSection === 'settings' ? (
              <div className="hidden flex-1 sm:block sm:px-6" aria-hidden />
            ) : (
              <div className="relative mx-auto w-full max-w-xl sm:mx-0 sm:flex-1 sm:px-6">
                <Search
                  className={`pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 ${
                    isLight ? 'text-slate-400' : 'text-slate-500'
                  }`}
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
                  className={`w-full rounded-xl border py-2 pl-10 pr-4 text-sm transition focus:outline-none focus:ring-2 ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                      : 'border-white/10 bg-slate-900/80 text-slate-200 placeholder:text-slate-500 focus:border-indigo-500/50 focus:ring-indigo-500/30'
                  }`}
                />
              </div>
            )}

            <div className="flex items-center justify-end gap-2 sm:gap-3">
              {/* Theme Toggle Button */}
              <button
                type="button"
                onClick={toggleTheme}
                className={`flex h-9 w-9 items-center justify-center rounded-xl border transition ${
                  isLight
                    ? 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                    : 'border-white/10 bg-slate-900/80 text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
                title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
                aria-label="Toggle Theme"
              >
                {isLight ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              </button>

              <button
                type="button"
                className={`flex h-9 w-9 items-center justify-center rounded-xl border transition ${
                  isLight
                    ? 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                    : 'border-white/10 bg-slate-900/80 text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" strokeWidth={1.75} />
              </button>

              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white shadow-xs">
                A
              </div>
              <span className={`hidden text-sm font-semibold sm:inline ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>Admin</span>

              <button
                type="button"
                onClick={handleLogout}
                className={`rounded-xl border px-3.5 py-1.5 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 hover:text-slate-900 shadow-xs'
                    : 'border-white/15 text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 space-y-8 px-4 py-8 sm:px-6">
          {/* Page header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-center gap-4">
              {(viewMode === 'candidates' || viewMode === 'report') && (
                <button
                  type="button"
                  onClick={viewMode === 'report' ? handleBackFromReport : handleBackFromCandidates}
                  className={`shrink-0 rounded-xl border p-2 transition ${
                    isLight
                      ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-xs'
                      : 'border-white/15 text-slate-300 hover:bg-white/5 hover:text-white'
                  }`}
                  aria-label="Back"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
              )}
              <div>
                <h1 className={`text-2xl font-extrabold tracking-tight sm:text-3xl ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  {pageTitle}
                </h1>
                <p className={`mt-1 text-sm ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  {pageSubtitle}
                </p>
              </div>
            </div>

            {(activeSection === 'dashboard' || activeSection === 'jobs') && !showCreateForm && viewMode === 'list' && (
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(true);
                  setError('');
                  setSuccess('');
                }}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-700"
              >
                <Plus className="h-4 w-4" strokeWidth={2.5} />
                Create Job Post
              </button>
            )}
          </div>

          {error && (
            <div className={`rounded-xl border px-4 py-3 text-sm font-medium ${
              isLight ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-red-400/30 bg-red-500/10 text-red-200'
            }`}>
              {error}
            </div>
          )}
          {success && (
            <div className={`rounded-xl border px-4 py-3 text-sm font-medium ${
              isLight ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200'
            }`}>
              {success}
            </div>
          )}

          {/* Stats KPI Cards */}
          {activeSection === 'dashboard' && (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {statCards.map((card) => (
                <div
                  key={card.label}
                  className={`rounded-2xl border p-5 transition-all ${
                    isLight
                      ? 'bg-white border-slate-200/90 shadow-xs hover:shadow-md hover:border-slate-300'
                      : 'bg-slate-900/50 border-white/10 hover:border-white/15'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl ${card.iconBg}`}
                    >
                      <card.icon className="h-5 w-5" strokeWidth={1.75} />
                    </div>
                    <span className={`max-w-[58%] text-right rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${
                      isLight
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                    }`}>
                      {card.trend}
                    </span>
                  </div>
                  <p className={`mt-4 text-3xl font-extrabold tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    {card.value}
                  </p>
                  <p className={`mt-1 text-xs font-semibold uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
                    {card.label}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Create form */}
          {(activeSection === 'dashboard' || activeSection === 'jobs') && showCreateForm && (
            <div className={`rounded-2xl border p-6 shadow-xs ${
              isLight ? 'bg-white border-slate-200' : 'bg-slate-900/50 border-white/10'
            }`}>
              <div className="mb-6 flex items-center justify-between">
                <h2 className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  New Job Post
                </h2>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className={`rounded-lg p-2 transition ${
                    isLight ? 'text-slate-400 hover:bg-slate-100 hover:text-slate-700' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>
              <form onSubmit={handleCreatePost} className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                    isLight ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    Job title *
                  </label>
                  <input
                    type="text"
                    value={newPost.title}
                    onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                    placeholder="e.g. Senior Backend Engineer"
                    className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                      isLight
                        ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                        : 'border-white/10 bg-[#0B1120] text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:ring-indigo-500/30'
                    }`}
                    required
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                    isLight ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    Description
                  </label>
                  <textarea
                    value={newPost.description}
                    onChange={(e) =>
                      setNewPost({ ...newPost, description: e.target.value })
                    }
                    placeholder="Brief job description, responsibilities, requirements…"
                    rows={3}
                    className={`w-full resize-none rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                      isLight
                        ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                        : 'border-white/10 bg-[#0B1120] text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:ring-indigo-500/30'
                    }`}
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                    isLight ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    Required skills *
                  </label>
                  <input
                    type="text"
                    value={newPost.required_skills}
                    onChange={(e) =>
                      setNewPost({ ...newPost, required_skills: e.target.value })
                    }
                    placeholder="Python, Docker, PostgreSQL, React"
                    className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                      isLight
                        ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                        : 'border-white/10 bg-[#0B1120] text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:ring-indigo-500/30'
                    }`}
                    required
                  />
                  <p className="mt-1 text-xs text-slate-500">Separate skills with commas</p>
                </div>
                <div>
                  <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                    isLight ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    Status
                  </label>
                  <select
                    value={newPost.status}
                    onChange={(e) => setNewPost({ ...newPost, status: e.target.value })}
                    className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                      isLight
                        ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                        : 'border-white/10 bg-[#0B1120] text-white focus:border-indigo-500/50 focus:ring-indigo-500/30'
                    }`}
                  >
                    {JOB_STATUS_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                    isLight ? 'text-slate-600' : 'text-slate-400'
                  }`}>
                    Domain
                  </label>
                  <input
                    type="text"
                    value={newPost.domain}
                    onChange={(e) => setNewPost({ ...newPost, domain: e.target.value })}
                    placeholder="e.g. Computing / Cloud / AI"
                    className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                      isLight
                        ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                        : 'border-white/10 bg-[#0B1120] text-white placeholder:text-slate-500 focus:border-indigo-500/50 focus:ring-indigo-500/30'
                    }`}
                  />
                </div>
                <div className="flex flex-wrap gap-3 sm:col-span-2 pt-2">
                  <button
                    type="submit"
                    disabled={creating}
                    className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {creating ? 'Creating…' : 'Create Job Post'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className={`rounded-xl border px-6 py-2.5 text-sm font-semibold transition ${
                      isLight ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50' : 'border-white/15 text-slate-300 hover:bg-white/5'
                    }`}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Users Table */}
          {activeSection === 'users' && (
            <section className={`rounded-2xl border shadow-xs overflow-hidden ${
              isLight ? 'bg-white border-slate-200' : 'bg-slate-900/40 border-white/10'
            }`}>
              <div className={`flex flex-col gap-4 border-b p-5 sm:flex-row sm:items-center sm:justify-between ${
                isLight ? 'border-slate-200 bg-slate-50/50' : 'border-white/10'
              }`}>
                <div className="flex items-center gap-2">
                  <h2 className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>All Registered Users</h2>
                  <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                    isLight ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-indigo-400/40 bg-indigo-500/15 text-indigo-200'
                  }`}>
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
                      <tr className={`border-b text-[11px] font-semibold uppercase tracking-wider ${
                        isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'border-white/10 text-slate-500'
                      }`}>
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
                          className={`border-b transition ${
                            isLight ? 'border-slate-100 hover:bg-slate-50/80' : 'border-white/5 hover:bg-white/[0.03]'
                          }`}
                        >
                          <td className={`px-5 py-4 align-top font-medium ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>{u.email}</td>
                          <td className={`px-5 py-4 align-top ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                            {u.full_name || '—'}
                          </td>
                          <td className={`px-5 py-4 align-top ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                            {u.username || '—'}
                          </td>
                          <td className={`px-5 py-4 align-top ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
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
                              <span className="font-semibold text-emerald-600">Yes</span>
                            ) : (
                              <span className="text-slate-400">No</span>
                            )}
                          </td>
                          <td className="px-5 py-4 align-top">
                            <span className={isLight ? 'text-slate-700 font-medium' : 'text-slate-300'}>{u.job_role || '—'}</span>
                            <span className="mt-1 block text-[11px] text-slate-500">
                              {u.skills_count != null ? `${u.skills_count} skills` : ''}
                            </span>
                          </td>
                          <td className="px-5 py-4 align-top">
                            {u.is_active !== false ? (
                              <span className="font-semibold text-emerald-600">Active</span>
                            ) : (
                              <span className="font-semibold text-amber-600">Inactive</span>
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
            <div className={`space-y-6 rounded-2xl border p-6 shadow-xs ${
              isLight ? 'bg-white border-slate-200 text-slate-900' : 'bg-slate-900/40 border-white/10 text-white'
            }`}>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  API base URL
                </p>
                <p className={`mt-1 font-mono text-sm ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                  {process.env.NEXT_PUBLIC_API_URL ||
                    'Same origin (relative /api or configured proxy)'}
                </p>
              </div>
              <div className="border-t pt-4 border-slate-100">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Theme Preference
                </p>
                <div className="mt-2 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setTheme('light');
                      localStorage.setItem('hiresight_admin_theme', 'light');
                    }}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold border transition ${
                      isLight ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs' : 'border-slate-700 text-slate-300 hover:bg-white/5'
                    }`}
                  >
                    White & Professional
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setTheme('dark');
                      localStorage.setItem('hiresight_admin_theme', 'dark');
                    }}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold border transition ${
                      !isLight ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs' : 'border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    Executive Dark Mode
                  </button>
                </div>
              </div>
              <div className="border-t pt-4 border-slate-100">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Admin Session
                </p>
                <button
                  type="button"
                  onClick={handleLogout}
                  className={`mt-2 rounded-xl border px-4 py-2 text-sm font-semibold transition ${
                    isLight
                      ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-xs'
                      : 'border-white/15 text-slate-200 hover:bg-white/5'
                  }`}
                >
                  Log out of admin
                </button>
              </div>
            </div>
          )}

          {/* Candidates Tab View */}
          {activeSection === 'candidates' && viewMode === 'list' && (
            <CandidateAssessmentRoster theme={theme} onViewReport={handleViewReport} />
          )}

          {/* Job-specific Candidates View */}
          {(activeSection === 'dashboard' || activeSection === 'jobs') && viewMode === 'candidates' && selectedJobForCandidates && (
            <JobCandidatesList
              theme={theme}
              jobPostId={selectedJobForCandidates.id}
              onViewReport={handleViewReport}
            />
          )}

          {/* Full Report View */}
          {viewMode === 'report' && reportData && (
            <RecruiterReportViewer
              theme={theme}
              report={reportData.recruiter_report}
              sessionId={reportData.session_id}
            />
          )}

          {/* Dashboard Tab: Candidate Roster Section */}
          {activeSection === 'dashboard' && viewMode === 'list' && (
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    Candidate Assessment Roster
                  </h2>
                  <p className={`text-xs ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                    Real-time candidate evaluation list with multi-criteria filters and 5-dimensional scores
                  </p>
                </div>
              </div>
              <CandidateAssessmentRoster theme={theme} onViewReport={handleViewReport} />
            </section>
          )}

          {/* Job posts table */}
          {activeSection === 'jobs' && viewMode === 'list' && (
          <section className={`rounded-2xl border shadow-xs overflow-hidden ${
            isLight ? 'bg-white border-slate-200' : 'bg-slate-900/40 border-white/10'
          }`}>
            <div className={`flex flex-col gap-4 border-b p-5 sm:flex-row sm:items-center sm:justify-between ${
              isLight ? 'border-slate-200 bg-slate-50/50' : 'border-white/10'
            }`}>
              <div className="flex items-center gap-2">
                <h2 className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>Job Posts</h2>
                <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                  isLight ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-indigo-400/40 bg-indigo-500/15 text-indigo-200'
                }`}>
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
                        ? isLight
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'bg-white/10 text-white'
                        : isLight
                        ? 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
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
                    <tr className={`border-b text-[11px] font-semibold uppercase tracking-wider ${
                      isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'border-white/10 text-slate-500'
                    }`}>
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
                          className={`border-b transition ${
                            isLight ? 'border-slate-100 hover:bg-slate-50/80' : 'border-white/5 hover:bg-white/[0.03]'
                          }`}
                        >
                          <td className="px-5 py-4 align-top">
                            <p className={`font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{post.title}</p>
                            <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{sub}</p>
                            {post.domain && (
                              <span className={`mt-2 inline-block rounded-md border px-2 py-0.5 text-[10px] font-medium ${
                                isLight ? 'border-slate-200 bg-slate-100 text-slate-600' : 'border-white/10 bg-white/5 text-slate-400'
                              }`}>
                                {post.domain}
                              </span>
                            )}
                          </td>
                          <td className={`px-5 py-4 align-top ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
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
                                onClick={() => handleViewCandidates(post)}
                                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-emerald-700"
                                title="View candidates who applied and completed interviews"
                              >
                                <UserCheck className="h-3.5 w-3.5" strokeWidth={2} />
                                Candidates ({post.applicant_count || 0})
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setViewJob(post);
                                  setError('');
                                }}
                                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-indigo-700"
                              >
                                <Eye className="h-3.5 w-3.5" strokeWidth={2} />
                                View
                              </button>
                              <button
                                type="button"
                                onClick={() => openEdit(post)}
                                className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                                  isLight
                                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-xs'
                                    : 'border-white/15 text-slate-200 hover:bg-white/5'
                                }`}
                              >
                                <Pencil className="h-3.5 w-3.5" strokeWidth={2} />
                                Edit
                              </button>
                              <button
                                type="button"
                                disabled={deletingId === post.id}
                                onClick={() => handleDeletePost(post)}
                                className={`inline-flex items-center justify-center rounded-lg border p-1.5 transition disabled:opacity-50 ${
                                  isLight
                                    ? 'border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100'
                                    : 'border-red-400/30 text-red-300 hover:bg-red-500/10'
                                }`}
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
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="view-job-title"
        >
          <div className={`max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border p-6 shadow-2xl ${
            isLight ? 'bg-white border-slate-200 text-slate-900' : 'bg-[#0d1526] border-white/10 text-white'
          }`}>
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h3 id="view-job-title" className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  {viewJob.title}
                </h3>
                {viewJob.domain && (
                  <span className={`mt-2 inline-block rounded-md border px-2 py-0.5 text-[11px] font-medium ${
                    isLight ? 'border-slate-200 bg-slate-100 text-slate-600' : 'border-white/10 text-slate-400'
                  }`}>
                    {viewJob.domain}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setViewJob(null)}
                className={`rounded-lg p-2 transition ${
                  isLight ? 'text-slate-400 hover:bg-slate-100 hover:text-slate-700' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
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
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Description
                </p>
                <p className={`whitespace-pre-wrap text-sm leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                  {viewJob.description}
                </p>
              </div>
            ) : (
              <p className="mb-4 text-sm italic text-slate-500">No description provided.</p>
            )}
            {viewJob.required_skills?.length > 0 && (
              <div>
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Required skills
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {viewJob.required_skills.map((skill) => (
                    <span
                      key={skill}
                      className={`rounded-md border px-2 py-1 text-[11px] font-medium ${
                        isLight ? 'border-slate-200 bg-slate-100 text-slate-700' : 'border-white/10 bg-white/5 text-slate-300'
                      }`}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className={`mt-6 flex flex-wrap gap-2 border-t pt-4 ${isLight ? 'border-slate-100' : 'border-white/10'}`}>
              <button
                type="button"
                onClick={() => {
                  openEdit(viewJob);
                  setViewJob(null);
                }}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-indigo-700"
              >
                Edit this job
              </button>
              <button
                type="button"
                onClick={() => setViewJob(null)}
                className={`rounded-xl border px-4 py-2 text-sm font-medium transition ${
                  isLight ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50' : 'border-white/15 text-slate-300 hover:bg-white/5'
                }`}
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
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-job-title"
        >
          <div className={`max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border p-6 shadow-2xl ${
            isLight ? 'bg-white border-slate-200 text-slate-900' : 'bg-[#0d1526] border-white/10 text-white'
          }`}>
            <div className="mb-6 flex items-center justify-between">
              <h3 id="edit-job-title" className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                Edit Job Post
              </h3>
              <button
                type="button"
                onClick={() => setEditJob(null)}
                className={`rounded-lg p-2 transition ${
                  isLight ? 'text-slate-400 hover:bg-slate-100 hover:text-slate-700' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleUpdatePost} className="space-y-4">
              <div>
                <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                  isLight ? 'text-slate-600' : 'text-slate-400'
                }`}>
                  Job title *
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                      : 'border-white/10 bg-[#0B1120] text-white focus:border-indigo-500/50 focus:ring-indigo-500/30'
                  }`}
                  required
                />
              </div>
              <div>
                <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                  isLight ? 'text-slate-600' : 'text-slate-400'
                }`}>
                  Description
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                  rows={4}
                  className={`w-full resize-none rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                      : 'border-white/10 bg-[#0B1120] text-white focus:border-indigo-500/50 focus:ring-indigo-500/30'
                  }`}
                />
              </div>
              <div>
                <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                  isLight ? 'text-slate-600' : 'text-slate-400'
                }`}>
                  Required skills *
                </label>
                <input
                  type="text"
                  value={editForm.required_skills}
                  onChange={(e) =>
                    setEditForm({ ...editForm, required_skills: e.target.value })
                  }
                  placeholder="Python, Docker, AWS"
                  className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                      : 'border-white/10 bg-[#0B1120] text-white focus:border-indigo-500/50 focus:ring-indigo-500/30'
                  }`}
                  required
                />
                <p className="mt-1 text-xs text-slate-500">Separate skills with commas</p>
              </div>
              <div>
                <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                  isLight ? 'text-slate-600' : 'text-slate-400'
                }`}>
                  Status
                </label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                      : 'border-white/10 bg-[#0B1120] text-white focus:border-indigo-500/50 focus:ring-indigo-500/30'
                  }`}
                >
                  {JOB_STATUS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                  isLight ? 'text-slate-600' : 'text-slate-400'
                }`}>
                  Domain
                </label>
                <input
                  type="text"
                  value={editForm.domain}
                  onChange={(e) => setEditForm({ ...editForm, domain: e.target.value })}
                  className={`w-full rounded-xl border px-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                      : 'border-white/10 bg-[#0B1120] text-white focus:border-indigo-500/50 focus:ring-indigo-500/30'
                  }`}
                />
              </div>
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-700 disabled:opacity-50"
                >
                  {savingEdit ? 'Saving…' : 'Save changes'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditJob(null)}
                  className={`rounded-xl border px-6 py-2.5 text-sm font-medium transition ${
                    isLight ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50' : 'border-white/15 text-slate-300 hover:bg-white/5'
                  }`}
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
