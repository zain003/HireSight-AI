/**
 * Candidate Assessment Roster Component
 * Implements Issue 02 (Part 1, 2, 4) for HireSIGHT Admin Dashboard.
 * Features:
 * - Ultra-clean executive White & Professional theme with Dark Mode support
 * - Server-side search & multi-criteria filtering (Status, Score Range, Role, Recommendation, Date Range)
 * - URL query synchronization (bookmarkable/shareable filtered views)
 * - Column sorting (Score, Date, Name, Status) & Server-side pagination
 * - 5-Dimensional score badges, hire recommendation indicators, and full report triggers
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/router';
import {
  Search,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Calendar,
  SlidersHorizontal,
  RotateCcw,
  CheckCircle2,
  Clock,
  UserX,
  FileText,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Users,
  Award,
  AlertCircle,
  X,
  ShieldAlert,
  AlertOctagon,
} from 'lucide-react';
import adminDashboardService from '@/services/adminDashboardService';

const STATUS_OPTIONS = [
  { id: 'all', label: 'All Statuses', color: 'slate' },
  { id: 'completed', label: 'Completed', color: 'emerald' },
  { id: 'in_progress', label: 'In Progress', color: 'sky' },
  { id: 'blacklisted', label: 'Blacklisted (Cheating)', color: 'rose' },
  { id: 'not_started', label: 'Not Started', color: 'slate' },
];

const RECOMMENDATION_OPTIONS = [
  { id: 'all', label: 'All Recommendations' },
  { id: 'Strong Fit', label: 'Strong Fit', color: 'emerald' },
  { id: 'Potential Fit', label: 'Potential Fit', color: 'indigo' },
  { id: 'Needs Growth', label: 'Needs Growth', color: 'amber' },
  { id: 'Not a Fit', label: 'Not a Fit', color: 'red' },
];

const SORT_OPTIONS = [
  { id: 'date_desc', label: 'Date: Newest First' },
  { id: 'date_asc', label: 'Date: Oldest First' },
  { id: 'score_desc', label: 'Score: Highest First' },
  { id: 'score_asc', label: 'Score: Lowest First' },
  { id: 'name_asc', label: 'Name: A → Z' },
  { id: 'name_desc', label: 'Name: Z → A' },
  { id: 'status', label: 'Status' },
];

export default function CandidateAssessmentRoster({ onViewReport, jobPostId = null, theme = 'light' }) {
  const router = useRouter();
  const isLight = theme === 'light';

  // ── State ─────────────────────────────────────────────────────────────────
  const [data, setData] = useState({
    items: [],
    total_count: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
    available_roles: [],
    available_recommendations: [],
    status_counts: { total: 0, completed: 0, in_progress: 0, not_started: 0 },
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Filters State
  const [search, setSearch] = useState('');
  const [selectedStatuses, setSelectedStatuses] = useState([]);
  const [selectedRole, setSelectedRole] = useState('all');
  const [minScore, setMinScore] = useState('');
  const [maxScore, setMaxScore] = useState('');
  const [selectedRecommendation, setSelectedRecommendation] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortBy, setSortBy] = useState('date_desc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Debounce search input
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const searchTimeoutRef = useRef(null);

  const isInitialUrlSyncDone = useRef(false);

  // ── Sync from URL Query on Mount ──────────────────────────────────────────
  useEffect(() => {
    if (!router.isReady || isInitialUrlSyncDone.current) return;

    const q = router.query;
    if (q.search) {
      setSearch(String(q.search));
      setDebouncedSearch(String(q.search));
    }
    if (q.status) {
      const statuses = Array.isArray(q.status) ? q.status : [q.status];
      setSelectedStatuses(statuses.filter((s) => s !== 'all'));
    }
    if (q.role) setSelectedRole(String(q.role));
    if (q.min_score) setMinScore(String(q.min_score));
    if (q.max_score) setMaxScore(String(q.max_score));
    if (q.recommendation) setSelectedRecommendation(String(q.recommendation));
    if (q.start_date) setStartDate(String(q.start_date));
    if (q.end_date) setEndDate(String(q.end_date));
    if (q.sort_by) setSortBy(String(q.sort_by));
    if (q.page) setPage(Math.max(1, parseInt(q.page, 10) || 1));
    if (q.page_size) setPageSize(Math.max(1, parseInt(q.page_size, 10) || 10));

    if (q.min_score || q.max_score || q.start_date || q.end_date || q.recommendation) {
      setShowAdvancedFilters(true);
    }

    isInitialUrlSyncDone.current = true;
  }, [router.isReady, router.query]);

  // ── Debounce Search Input ─────────────────────────────────────────────────
  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(1);
    }, 350);
  };

  const handleClearSearch = () => {
    setSearch('');
    setDebouncedSearch('');
    setPage(1);
  };

  // ── Fetch Candidate Roster ────────────────────────────────────────────────
  const fetchRoster = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        search: debouncedSearch.trim() || undefined,
        status: selectedStatuses.length > 0 ? selectedStatuses : undefined,
        role: selectedRole !== 'all' ? selectedRole : undefined,
        min_score: minScore !== '' ? parseFloat(minScore) : undefined,
        max_score: maxScore !== '' ? parseFloat(maxScore) : undefined,
        recommendation:
          selectedRecommendation !== 'all' ? [selectedRecommendation] : undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        sort_by: sortBy,
        page,
        page_size: pageSize,
        job_post_id: jobPostId || undefined,
      };

      const result = await adminDashboardService.getCandidateRoster(params);
      setData(result);
    } catch (err) {
      console.error('Failed to load candidate roster:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load candidate records');
    } finally {
      setLoading(false);
    }
  }, [
    debouncedSearch,
    selectedStatuses,
    selectedRole,
    minScore,
    maxScore,
    selectedRecommendation,
    startDate,
    endDate,
    sortBy,
    page,
    pageSize,
    jobPostId,
  ]);

  // Trigger fetch when dependencies change
  useEffect(() => {
    fetchRoster();
  }, [fetchRoster]);

  // ── Sync State to URL Query ───────────────────────────────────────────────
  useEffect(() => {
    if (jobPostId) return;
    if (!isInitialUrlSyncDone.current || !router.isReady) return;

    const query = { ...router.query };

    // Update query params
    if (debouncedSearch.trim()) query.search = debouncedSearch.trim();
    else delete query.search;

    if (selectedStatuses.length > 0) query.status = selectedStatuses;
    else delete query.status;

    if (selectedRole && selectedRole !== 'all') query.role = selectedRole;
    else delete query.role;

    if (minScore !== '') query.min_score = minScore;
    else delete query.min_score;

    if (maxScore !== '') query.max_score = maxScore;
    else delete query.max_score;

    if (selectedRecommendation && selectedRecommendation !== 'all')
      query.recommendation = selectedRecommendation;
    else delete query.recommendation;

    if (startDate) query.start_date = startDate;
    else delete query.start_date;

    if (endDate) query.end_date = endDate;
    else delete query.end_date;

    if (sortBy && sortBy !== 'date_desc') query.sort_by = sortBy;
    else delete query.sort_by;

    if (page > 1) query.page = String(page);
    else delete query.page;

    if (pageSize !== 10) query.page_size = String(pageSize);
    else delete query.page_size;

    const keysBefore = Object.keys(router.query).sort();
    const keysAfter = Object.keys(query).sort();
    let isChanged = keysBefore.length !== keysAfter.length;
    if (!isChanged) {
      for (const k of keysAfter) {
        if (String(router.query[k]) !== String(query[k])) {
          isChanged = true;
          break;
        }
      }
    }

    if (isChanged) {
      router.replace(
        {
          pathname: router.pathname,
          query,
        },
        undefined,
        { shallow: true }
      );
    }
  }, [
    debouncedSearch,
    selectedStatuses,
    selectedRole,
    minScore,
    maxScore,
    selectedRecommendation,
    startDate,
    endDate,
    sortBy,
    page,
    pageSize,
    router.isReady,
    jobPostId,
  ]);

  // ── Filter Handlers ───────────────────────────────────────────────────────
  const handleToggleStatus = (statusId) => {
    setPage(1);
    if (statusId === 'all') {
      setSelectedStatuses([]);
      return;
    }
    setSelectedStatuses((prev) => {
      if (prev.includes(statusId)) {
        return prev.filter((s) => s !== statusId);
      } else {
        return [...prev, statusId];
      }
    });
  };

  const handleClearAllFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setSelectedStatuses([]);
    setSelectedRole('all');
    setMinScore('');
    setMaxScore('');
    setSelectedRecommendation('all');
    setStartDate('');
    setEndDate('');
    setSortBy('date_desc');
    setPage(1);
  };

  const activeFiltersCount =
    (debouncedSearch ? 1 : 0) +
    (selectedStatuses.length > 0 ? 1 : 0) +
    (selectedRole !== 'all' ? 1 : 0) +
    (minScore !== '' ? 1 : 0) +
    (maxScore !== '' ? 1 : 0) +
    (selectedRecommendation !== 'all' ? 1 : 0) +
    (startDate ? 1 : 0) +
    (endDate ? 1 : 0);

  // ── Helpers ───────────────────────────────────────────────────────────────
  const getStatusBadge = (status) => {
    const s = (status || 'not_started').toLowerCase();
    switch (s) {
      case 'completed':
        return (
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
            isLight ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
          }`}>
            <CheckCircle2 className="h-3.5 w-3.5" />
            Completed
          </span>
        );
      case 'in_progress':
        return (
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
            isLight ? 'border-sky-200 bg-sky-50 text-sky-700' : 'border-sky-500/30 bg-sky-500/10 text-sky-300'
          }`}>
            <Clock className="h-3.5 w-3.5 animate-spin" />
            In Progress
          </span>
        );
      case 'blacklisted':
      case 'violated':
      case 'cancelled':
        return (
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-bold ${
            isLight ? 'border-rose-300 bg-rose-50 text-rose-700' : 'border-rose-500/40 bg-rose-500/15 text-rose-300'
          }`}>
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
            Blacklisted (Cheating)
          </span>
        );
      case 'abandoned':
        return (
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
            isLight ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
          }`}>
            <AlertCircle className="h-3.5 w-3.5" />
            Abandoned
          </span>
        );
      case 'not_started':
      default:
        return (
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
            isLight ? 'border-slate-200 bg-slate-100 text-slate-600' : 'border-slate-700 bg-slate-800/80 text-slate-400'
          }`}>
            <UserX className="h-3.5 w-3.5" />
            Not Started
          </span>
        );
    }
  };

  const getFitBadge = (recommendation) => {
    if (!recommendation) return null;
    const rec = recommendation.trim();
    if (rec.toLowerCase().includes('blacklisted') || rec.toLowerCase().includes('cheating')) {
      return (
        <span className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-bold ${
          isLight ? 'border-rose-300 bg-rose-50 text-rose-700' : 'border-rose-500/40 bg-rose-500/15 text-rose-300'
        }`}>
          <ShieldAlert className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
          {rec}
        </span>
      );
    }
    if (rec === 'Strong Fit' || rec === 'Strong Hire') {
      return (
        <span className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-semibold ${
          isLight ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-emerald-500/30 bg-emerald-500/15 text-emerald-200'
        }`}>
          <Sparkles className="h-3.5 w-3.5 text-emerald-500" />
          {rec}
        </span>
      );
    }
    if (rec === 'Potential Fit' || rec === 'Hire') {
      return (
        <span className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-semibold ${
          isLight ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-indigo-500/30 bg-indigo-500/15 text-indigo-200'
        }`}>
          <Award className="h-3.5 w-3.5 text-indigo-500" />
          {rec}
        </span>
      );
    }
    if (rec === 'Needs Growth' || rec === 'Maybe') {
      return (
        <span className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-semibold ${
          isLight ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-amber-500/30 bg-amber-500/15 text-amber-200'
        }`}>
          <AlertCircle className="h-3.5 w-3.5 text-amber-500" />
          {rec}
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-semibold ${
        isLight ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-red-500/30 bg-red-500/15 text-red-200'
      }`}>
        <UserX className="h-3.5 w-3.5 text-rose-500" />
        {rec}
      </span>
    );
  };

  const getScoreDisplay = (score) => {
    if (score === null || score === undefined) {
      return <span className="text-xs text-slate-400 font-mono">—</span>;
    }
    const val = Math.round(Number(score));
    let colorClass = isLight
      ? 'text-rose-700 border-rose-200 bg-rose-50'
      : 'text-red-400 border-red-500/30 bg-red-500/10';

    if (val >= 80) {
      colorClass = isLight
        ? 'text-emerald-700 border-emerald-200 bg-emerald-50'
        : 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    } else if (val >= 60) {
      colorClass = isLight
        ? 'text-amber-700 border-amber-200 bg-amber-50'
        : 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    }

    return (
      <div className="flex items-center gap-2">
        <div
          className={`inline-flex h-8 w-11 items-center justify-center rounded-lg border text-sm font-bold ${colorClass}`}
        >
          {val}
        </div>
        <span className="text-[11px] text-slate-400 font-mono">/100</span>
      </div>
    );
  };

  const formatDate = (isoString) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return '—';
    }
  };

  const counts = data.status_counts || { total: 0, completed: 0, in_progress: 0, not_started: 0 };

  return (
    <div className="space-y-6">
      {/* ── KPI Stat Cards ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
        <div className={`rounded-2xl border p-4 sm:p-5 transition-all ${
          isLight
            ? 'bg-white border-slate-200 shadow-xs hover:shadow-md hover:border-slate-300'
            : 'bg-slate-900/50 border-white/10 hover:border-white/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Roster
            </span>
            <div className={`rounded-lg p-1.5 ${isLight ? 'bg-indigo-50 text-indigo-600' : 'text-indigo-400'}`}>
              <Users className="h-4 w-4" />
            </div>
          </div>
          <p className={`mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
            {counts.total}
          </p>
          <span className="mt-1 block text-[11px] text-slate-500">Candidates evaluated</span>
        </div>

        <div className={`rounded-2xl border p-4 sm:p-5 transition-all ${
          isLight
            ? 'bg-white border-emerald-200/80 shadow-xs hover:shadow-md'
            : 'bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-semibold uppercase tracking-wider ${isLight ? 'text-emerald-700' : 'text-emerald-300'}`}>
              Completed
            </span>
            <div className={`rounded-lg p-1.5 ${isLight ? 'bg-emerald-50 text-emerald-600' : 'text-emerald-400'}`}>
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <p className={`mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
            {counts.completed}
          </p>
          <span className={`mt-1 block text-[11px] ${isLight ? 'text-emerald-600/80' : 'text-emerald-400/70'}`}>
            Full reports available
          </span>
        </div>

        <div className={`rounded-2xl border p-4 sm:p-5 transition-all ${
          isLight
            ? 'bg-white border-sky-200/80 shadow-xs hover:shadow-md'
            : 'bg-sky-500/5 border-sky-500/20 hover:border-sky-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-semibold uppercase tracking-wider ${isLight ? 'text-sky-700' : 'text-sky-300'}`}>
              In Progress
            </span>
            <div className={`rounded-lg p-1.5 ${isLight ? 'bg-sky-50 text-sky-600' : 'text-sky-400'}`}>
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <p className={`mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight ${isLight ? 'text-sky-700' : 'text-sky-400'}`}>
            {counts.in_progress}
          </p>
          <span className={`mt-1 block text-[11px] ${isLight ? 'text-sky-600/80' : 'text-sky-400/70'}`}>
            Active assessments
          </span>
        </div>

        <div className={`rounded-2xl border p-4 sm:p-5 transition-all ${
          isLight
            ? 'bg-white border-slate-200 shadow-xs hover:shadow-md'
            : 'bg-slate-900/40 border-slate-700/60 hover:border-slate-600'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Not Started
            </span>
            <div className={`rounded-lg p-1.5 ${isLight ? 'bg-slate-100 text-slate-600' : 'text-slate-500'}`}>
              <UserX className="h-4 w-4" />
            </div>
          </div>
          <p className={`mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
            {counts.not_started}
          </p>
          <span className="mt-1 block text-[11px] text-slate-500">Registered applicants</span>
        </div>
      </div>

      {/* ── Search and Filter Panel ─────────────────── */}
      <div className={`rounded-2xl border p-5 shadow-xs space-y-4 ${
        isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'
      }`}>
        {/* Top Filter Row: Search & Status Pills & Filter Toggle */}
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Search Box */}
          <div className="relative flex-1 max-w-xl">
            <Search
              className={`pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 ${
                isLight ? 'text-slate-400' : 'text-slate-400'
              }`}
              strokeWidth={2}
            />
            <input
              type="text"
              value={search}
              onChange={handleSearchChange}
              placeholder="Search candidates by name, email, role, or skills…"
              className={`w-full rounded-xl border py-2.5 pl-10 pr-10 text-sm transition focus:outline-none focus:ring-2 ${
                isLight
                  ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600 focus:ring-indigo-100'
                  : 'border-white/10 bg-slate-950/70 text-slate-100 placeholder:text-slate-500 focus:border-indigo-500/50 focus:ring-indigo-500/20'
              }`}
            />
            {search && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Status Multi-Select Toggle Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            {STATUS_OPTIONS.map((opt) => {
              const isSelected =
                opt.id === 'all'
                  ? selectedStatuses.length === 0
                  : selectedStatuses.includes(opt.id);
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => handleToggleStatus(opt.id)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : isLight
                      ? 'border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                      : 'border border-white/10 bg-slate-950/40 text-slate-400 hover:bg-white/5 hover:text-slate-200'
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}

            {/* Advanced Filters Toggle Button */}
            <button
              type="button"
              onClick={() => setShowAdvancedFilters((prev) => !prev)}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                showAdvancedFilters || activeFiltersCount > 0
                  ? isLight
                    ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                    : 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300'
                  : isLight
                  ? 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                  : 'border-white/10 bg-slate-950/40 text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              <span>Filters</span>
              {activeFiltersCount > 0 && (
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white">
                  {activeFiltersCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Expandable Advanced Filters Panel */}
        {showAdvancedFilters && (
          <div className={`border-t pt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 ${
            isLight ? 'border-slate-100' : 'border-white/10'
          }`}>
            {/* Target Role Selector */}
            <div>
              <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                isLight ? 'text-slate-600' : 'text-slate-400'
              }`}>
                Role / Position
              </label>
              <select
                value={selectedRole}
                onChange={(e) => {
                  setSelectedRole(e.target.value);
                  setPage(1);
                }}
                className={`w-full rounded-lg border px-3 py-2 text-xs transition focus:outline-none ${
                  isLight
                    ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600'
                    : 'border-white/10 bg-slate-950/70 text-slate-200 focus:border-indigo-500'
                }`}
              >
                <option value="all">All Target Roles</option>
                {(data.available_roles || []).map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            {/* Hire Recommendation Selector */}
            <div>
              <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                isLight ? 'text-slate-600' : 'text-slate-400'
              }`}>
                Recommendation
              </label>
              <select
                value={selectedRecommendation}
                onChange={(e) => {
                  setSelectedRecommendation(e.target.value);
                  setPage(1);
                }}
                className={`w-full rounded-lg border px-3 py-2 text-xs transition focus:outline-none ${
                  isLight
                    ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600'
                    : 'border-white/10 bg-slate-950/70 text-slate-200 focus:border-indigo-500'
                }`}
              >
                {RECOMMENDATION_OPTIONS.map((rec) => (
                  <option key={rec.id} value={rec.id}>
                    {rec.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Score Range Inputs */}
            <div>
              <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                isLight ? 'text-slate-600' : 'text-slate-400'
              }`}>
                Score Range (0–100)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="Min (e.g. 70)"
                  value={minScore}
                  onChange={(e) => {
                    setMinScore(e.target.value);
                    setPage(1);
                  }}
                  className={`w-full rounded-lg border px-3 py-2 text-xs transition focus:outline-none ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600'
                      : 'border-white/10 bg-slate-950/70 text-slate-200 placeholder:text-slate-600 focus:border-indigo-500'
                  }`}
                />
                <span className="text-slate-400">—</span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="Max (100)"
                  value={maxScore}
                  onChange={(e) => {
                    setMaxScore(e.target.value);
                    setPage(1);
                  }}
                  className={`w-full rounded-lg border px-3 py-2 text-xs transition focus:outline-none ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-indigo-600'
                      : 'border-white/10 bg-slate-950/70 text-slate-200 placeholder:text-slate-600 focus:border-indigo-500'
                  }`}
                />
              </div>
            </div>

            {/* Date Range Inputs */}
            <div>
              <label className={`mb-1.5 block text-xs font-semibold uppercase tracking-wider ${
                isLight ? 'text-slate-600' : 'text-slate-400'
              }`}>
                Activity Date Range
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => {
                    setStartDate(e.target.value);
                    setPage(1);
                  }}
                  className={`w-full rounded-lg border px-2.5 py-2 text-xs transition focus:outline-none ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600'
                      : 'border-white/10 bg-slate-950/70 text-slate-200 focus:border-indigo-500'
                  }`}
                />
                <span className="text-slate-400">—</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => {
                    setEndDate(e.target.value);
                    setPage(1);
                  }}
                  className={`w-full rounded-lg border px-2.5 py-2 text-xs transition focus:outline-none ${
                    isLight
                      ? 'border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:border-indigo-600'
                      : 'border-white/10 bg-slate-950/70 text-slate-200 focus:border-indigo-500'
                  }`}
                />
              </div>
            </div>
          </div>
        )}

        {/* Filter Summary & Sorting Bar */}
        <div className={`flex flex-col gap-2 border-t pt-3 sm:flex-row sm:items-center sm:justify-between ${
          isLight ? 'border-slate-100' : 'border-white/5'
        }`}>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
              Showing <strong className={isLight ? 'text-slate-900' : 'text-white'}>{data.items.length}</strong> of{' '}
              <strong className={isLight ? 'text-slate-900' : 'text-white'}>{data.total_count}</strong> matching candidates
            </span>
            {activeFiltersCount > 0 && (
              <button
                type="button"
                onClick={handleClearAllFilters}
                className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-semibold transition ${
                  isLight
                    ? 'border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                    : 'border-white/10 text-indigo-300 hover:bg-white/5 hover:text-white'
                }`}
              >
                <RotateCcw className="h-3 w-3" />
                Clear Filters
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition focus:outline-none ${
                isLight
                  ? 'border-slate-200 bg-slate-50 text-slate-800 focus:bg-white focus:border-indigo-600'
                  : 'border-white/10 bg-slate-950/70 text-slate-200 focus:border-indigo-500'
              }`}
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ── Error Banner ────────────────────────────────────────────────── */}
      {error && (
        <div className={`flex items-center justify-between rounded-xl border p-4 text-sm font-medium ${
          isLight
            ? 'border-rose-200 bg-rose-50 text-rose-800'
            : 'border-red-500/30 bg-red-500/10 text-red-200'
        }`}>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={fetchRoster}
            className="rounded-lg bg-rose-600 px-3 py-1 text-xs font-semibold text-white hover:bg-rose-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Candidate Table / List View ──────────────── */}
      <div className={`rounded-2xl border shadow-xs overflow-hidden ${
        isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10 shadow-xl backdrop-blur-md'
      }`}>
        {loading ? (
          <div className="flex flex-col items-center justify-center p-16 gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
            <p className={`text-sm font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Loading candidate records…</p>
          </div>
        ) : data.items.length === 0 ? (
          <div className="p-16 text-center">
            <Users className="mx-auto mb-3 h-12 w-12 text-slate-400" strokeWidth={1.2} />
            <h3 className={`text-base font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>No candidates match criteria</h3>
            <p className={`mt-1 text-sm ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
              Try adjusting search terms, clearing status filters, or widening score bounds.
            </p>
            {activeFiltersCount > 0 && (
              <button
                type="button"
                onClick={handleClearAllFilters}
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-indigo-700"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Reset All Filters
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-sm">
              <thead>
                <tr className={`border-b text-[11px] font-semibold uppercase tracking-wider ${
                  isLight ? 'bg-slate-50 border-slate-200 text-slate-600' : 'bg-slate-950/40 border-white/10 text-slate-400'
                }`}>
                  <th className="px-5 py-4">Candidate</th>
                  <th className="px-5 py-4">Role / Applied Job</th>
                  <th className="px-5 py-4">Status</th>
                  <th className="px-5 py-4">Date & Time</th>
                  <th className="px-5 py-4">Overall Score</th>
                  <th className="px-5 py-4">Recommendation</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className={isLight ? 'divide-y divide-slate-100' : 'divide-y divide-white/5'}>
                {data.items.map((item) => {
                  const isCompleted = (item.status || '').toLowerCase() === 'completed';
                  return (
                    <tr
                      key={item.session_id || item.user_id}
                      className={`transition group ${
                        isLight ? 'hover:bg-slate-50/80' : 'hover:bg-white/[0.03]'
                      }`}
                    >
                      {/* Candidate Name & Email */}
                      <td className="px-5 py-4 align-top">
                        <div className="flex items-center gap-3">
                          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-bold text-sm ${
                            isLight
                              ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                              : 'bg-indigo-500/20 text-indigo-300 border border-indigo-400/20'
                          }`}>
                            {(item.candidate_name || 'C').charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <p className={`font-semibold truncate transition ${
                              isLight
                                ? 'text-slate-900 group-hover:text-indigo-600'
                                : 'text-white group-hover:text-indigo-300'
                            }`}>
                              {item.candidate_name}
                            </p>
                            <p className={`text-xs truncate ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                              {item.email || (item.username ? `@${item.username}` : 'No email')}
                            </p>
                            {item.experience_years != null && (
                              <span className={`mt-1 inline-block text-[10px] font-medium ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
                                {item.experience_years} yrs exp
                              </span>
                            )}
                            {(item.violation_reason || item.blacklist_reason || item.is_blacklisted || (item.status || '').toLowerCase() === 'blacklisted') && (
                              <div className="mt-1.5 flex items-center gap-1 text-[11px] font-bold text-rose-600 dark:text-rose-400">
                                <AlertOctagon className="h-3 w-3 shrink-0" />
                                <span className="truncate max-w-[220px]" title={item.violation_reason || item.blacklist_reason || 'Cheating violation: tab switching detected.'}>
                                  {item.violation_reason || item.blacklist_reason || 'Cheating violation (Tab switched)'}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Target Role / Position */}
                      <td className="px-5 py-4 align-top">
                        <p className={`font-medium ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                          {item.job_post_title || item.job_role || 'Software Engineer'}
                        </p>
                        {item.skills && item.skills.length > 0 && (
                          <div className="mt-1.5 flex flex-wrap gap-1">
                            {item.skills.slice(0, 3).map((sk, idx) => (
                              <span
                                key={idx}
                                className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                                  isLight
                                    ? 'bg-slate-100 text-slate-700 border border-slate-200/60'
                                    : 'bg-slate-800/80 text-slate-300'
                                }`}
                              >
                                {sk}
                              </span>
                            ))}
                            {item.skills.length > 3 && (
                              <span className="text-[10px] text-slate-500">
                                +{item.skills.length - 3}
                              </span>
                            )}
                          </div>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-5 py-4 align-top">{getStatusBadge(item.status)}</td>

                      {/* Activity Date & Duration */}
                      <td className={`px-5 py-4 align-top text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                        <p className={`font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                          {formatDate(item.ended_at || item.started_at)}
                        </p>
                        {item.duration_minutes != null && (
                          <span className="text-[11px] text-slate-500">
                            Duration: {item.duration_minutes} min
                          </span>
                        )}
                      </td>

                      {/* Overall Score */}
                      <td className="px-5 py-4 align-top">{getScoreDisplay(item.overall_score)}</td>

                      {/* Hire Recommendation */}
                      <td className="px-5 py-4 align-top">
                        {item.hiring_recommendation ? (
                          getFitBadge(item.hiring_recommendation)
                        ) : (
                          <span className="text-xs text-slate-400 font-mono">—</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-4 align-top text-right">
                        {(isCompleted || (item.status || '').toLowerCase() === 'blacklisted' || item.is_blacklisted) && item.session_id ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => onViewReport(item.session_id)}
                              className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold text-white shadow-xs transition ${
                                (item.status || '').toLowerCase() === 'blacklisted' || item.is_blacklisted
                                  ? 'bg-rose-600 hover:bg-rose-700'
                                  : 'bg-indigo-600 hover:bg-indigo-700'
                              }`}
                              title={(item.status || '').toLowerCase() === 'blacklisted' || item.is_blacklisted ? 'Open Cheating Violation & Recruiter Dossier' : 'Open Full 5-Dimensional Recruiter Dossier'}
                            >
                              <FileText className="h-3.5 w-3.5" />
                              {(item.status || '').toLowerCase() === 'blacklisted' || item.is_blacklisted ? 'Violation Report' : 'View Report'}
                            </button>
                            <a
                              href={`/admin/candidates/${item.session_id}`}
                              target="_blank"
                              rel="noreferrer"
                              className={`rounded-xl border p-2 transition ${
                                isLight
                                  ? 'border-slate-200 text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                                  : 'border-white/10 text-slate-400 hover:bg-white/5 hover:text-white'
                              }`}
                              title="Open in new tab"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          </div>
                        ) : item.status === 'in_progress' ? (
                          <span className={`inline-block text-xs italic ${isLight ? 'text-sky-700 font-medium' : 'text-sky-400/80'}`}>
                            Interview active…
                          </span>
                        ) : (
                          <span className="inline-block text-xs italic text-slate-400">
                            Not yet taken
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Pagination Controls ────────────────────────────────────────── */}
        {!loading && data.total_count > 0 && (
          <div className={`flex flex-col gap-3 border-t px-5 py-4 sm:flex-row sm:items-center sm:justify-between ${
            isLight ? 'bg-slate-50/70 border-slate-200' : 'bg-slate-950/40 border-white/10'
          }`}>
            <div className="flex items-center gap-2">
              <span className={`text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(parseInt(e.target.value, 10));
                  setPage(1);
                }}
                className={`rounded-lg border px-2 py-1 text-xs transition focus:outline-none ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-800 focus:border-indigo-600'
                    : 'border-white/10 bg-slate-900 text-slate-200 focus:border-indigo-500'
                }`}
              >
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
              </select>
              <span className="text-xs text-slate-500">
                Page {data.page} of {data.total_pages}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className={`inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 shadow-xs'
                    : 'border-white/10 bg-slate-900 text-slate-300 hover:bg-white/5'
                }`}
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </button>

              {Array.from({ length: Math.min(5, data.total_pages) }, (_, idx) => {
                const pageNum = idx + 1;
                return (
                  <button
                    key={pageNum}
                    type="button"
                    onClick={() => setPage(pageNum)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      page === pageNum
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : isLight
                        ? 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-100'
                        : 'border border-white/10 bg-slate-900 text-slate-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                type="button"
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className={`inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 shadow-xs'
                    : 'border-white/10 bg-slate-900 text-slate-300 hover:bg-white/5'
                }`}
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
