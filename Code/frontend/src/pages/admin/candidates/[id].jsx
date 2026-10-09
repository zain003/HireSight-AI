/**
 * Candidate Full Report Page (Issue 02 - Part 3)
 * Dynamic Route: /admin/candidates/[id]
 * Renders complete single-source-of-truth dossier for recruiter assessment & hiring decisions.
 * Executive White & Professional Theme with instant Dark Mode support.
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Briefcase,
  Mail,
  User,
  ShieldAlert,
  AlertOctagon,
  Ban,
  FileWarning,
  Sparkles,
  Download,
  Share2,
  FileText,
  AlertCircle,
  Sun,
  Moon,
} from 'lucide-react';
import authService from '@/services/authService';
import adminDashboardService from '@/services/adminDashboardService';
import RecruiterReportViewer from '@/components/Interview/RecruiterReportViewer';

export default function CandidateReportPage() {
  const router = useRouter();
  const { id } = router.query;

  const [theme, setTheme] = useState('light');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);

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
    if (!router.isReady) return;
    if (!authService.isAuthenticated() || !authService.isAdminAuthenticated()) {
      router.push('/admin-login');
      return;
    }
    if (id) {
      loadReport(String(id));
    }
  }, [router.isReady, id]);

  const loadReport = async (sessionId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminDashboardService.getCandidateReport(sessionId);
      setData(res);
    } catch (err) {
      console.error('Failed to load candidate report:', err);
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to load interview report. Session may still be in progress or not found.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopyShareLink = () => {
    if (typeof window !== 'undefined') {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '—';
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '—';
    }
  };

  const candidate = data?.candidate_info || {};
  const interview = data?.interview_info || {};
  const recruiterReport = data?.recruiter_report || null;
  const fiveDim = recruiterReport?.five_dimension_scores || {};
  const overallScore = fiveDim.overall_composite_score ?? recruiterReport?.overall_score ?? null;
  const fitStatus = fiveDim.fit_status || recruiterReport?.fit_status || recruiterReport?.hiring_recommendation || 'Potential Fit';

  return (
    <>
      <Head>
        <title>
          {candidate.name ? `${candidate.name} — Candidate Report` : 'Candidate Report'} | HireSIGHT
        </title>
      </Head>

      <div className={`min-h-screen pb-16 transition-colors duration-200 ${
        isLight ? 'bg-[#F8FAFC] text-slate-900' : 'bg-[#0B1120] text-slate-100'
      }`}>
        {/* Sticky Top Header */}
        <header className={`sticky top-0 z-30 border-b backdrop-blur-md px-4 py-3 sm:px-8 transition-colors ${
          isLight ? 'border-slate-200 bg-white/95 text-slate-900 shadow-xs' : 'border-white/10 bg-[#0B1120]/90 text-slate-100'
        }`}>
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/admin-dashboard"
                className={`inline-flex items-center gap-2 rounded-xl border px-3.5 py-1.5 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 shadow-xs'
                    : 'border-white/10 bg-slate-900/80 text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Dashboard</span>
              </Link>

              <div className="hidden sm:block">
                <span className="text-xs text-slate-400">/</span>
                <span className={`ml-2 text-xs font-medium ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>Candidate Assessments</span>
                <span className="mx-2 text-xs text-slate-400">/</span>
                <span className={`text-xs font-bold truncate max-w-xs ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  {candidate.name || id}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Theme Toggle Button */}
              <button
                type="button"
                onClick={toggleTheme}
                className={`flex h-8 w-8 items-center justify-center rounded-xl border transition ${
                  isLight
                    ? 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    : 'border-white/10 bg-slate-900/80 text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
                title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
              >
                {isLight ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              </button>

              <button
                type="button"
                onClick={handleCopyShareLink}
                className={`inline-flex items-center gap-1.5 rounded-xl border px-3.5 py-1.5 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 shadow-xs'
                    : 'border-white/10 bg-slate-900/80 text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
                title="Copy shareable report URL"
              >
                <Share2 className="h-3.5 w-3.5" />
                <span>{copiedLink ? 'Link Copied!' : 'Share Dossier'}</span>
              </button>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center p-24 gap-4">
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
              <p className={`text-sm font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Loading comprehensive candidate dossier…</p>
            </div>
          ) : error ? (
            <div className={`rounded-2xl border p-8 text-center max-w-2xl mx-auto space-y-4 shadow-xs ${
              isLight ? 'border-rose-200 bg-rose-50' : 'border-red-500/30 bg-red-500/10'
            }`}>
              <ShieldAlert className="mx-auto h-12 w-12 text-rose-500" />
              <h2 className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>Unable to Load Report</h2>
              <p className={`text-sm ${isLight ? 'text-rose-800 font-medium' : 'text-red-200'}`}>{error}</p>
              <div className="pt-2 flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => id && loadReport(String(id))}
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-indigo-700"
                >
                  Retry
                </button>
                <Link
                  href="/admin-dashboard"
                  className={`rounded-xl border px-4 py-2 text-xs font-semibold transition ${
                    isLight ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-xs' : 'border-white/15 text-slate-300 hover:bg-white/5'
                  }`}
                >
                  Return to Dashboard
                </Link>
              </div>
            </div>
          ) : data ? (
            <>
              {/* Integrity Violation & Cheating Feedback Banner for Admin */}
              {(data.is_blacklisted || (data.status || '').toLowerCase() === 'blacklisted' || data.violation?.is_violated || candidate.is_blacklisted) && (
                <div className={`rounded-2xl border p-5 sm:p-6 shadow-md transition-all ${
                  isLight
                    ? 'border-rose-300 bg-rose-50/90 text-rose-950 shadow-rose-950/5'
                    : 'border-rose-500/40 bg-rose-950/40 text-rose-100 shadow-rose-950/30'
                }`}>
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-600 text-white shadow-md shadow-rose-600/30">
                      <ShieldAlert className="h-6 w-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-md border border-rose-300 bg-rose-100 dark:border-rose-500/30 dark:bg-rose-500/20 px-2.5 py-0.5 text-xs font-black uppercase tracking-wider text-rose-700 dark:text-rose-300">
                          Cheating & Integrity Violation
                        </span>
                        <h2 className="text-lg font-bold text-rose-700 dark:text-rose-300">
                          Candidate Blacklisted — Cheating Detected
                        </h2>
                      </div>
                      <p className="mt-1.5 text-sm font-semibold text-rose-900 dark:text-rose-200 leading-relaxed">
                        {data.violation?.violation_reason || candidate.blacklist_reason || 'Candidate switched tabs during the live proctored interview. Cheating violation recorded and candidate blacklisted.'}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-4 text-xs font-medium text-rose-700 dark:text-rose-300">
                        <span>• Violation Trigger: {data.violation?.violation_type || 'TAB_SWITCHING'}</span>
                        <span>• Action Taken: Interview cancelled & Score set to 0.0</span>
                        <span>• Candidate Account: Blacklisted Permanently</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Candidate Summary Header Hero Banner */}
              <div className={`rounded-2xl border p-6 shadow-xs ${
                isLight ? 'bg-white border-slate-200 text-slate-900' : 'bg-slate-900/60 border-white/10 text-white backdrop-blur-md shadow-xl'
              }`}>
                <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                  {/* Left: Avatar & Candidate Info */}
                  <div className="flex items-start gap-4">
                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 text-2xl font-black text-white shadow-md shadow-indigo-600/20">
                      {(candidate.name || 'C').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h1 className={`text-2xl font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>{candidate.name}</h1>
                        <span className={`rounded-full border px-3 py-0.5 text-xs font-semibold ${
                          isLight ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-indigo-400/40 bg-indigo-500/15 text-indigo-300'
                        }`}>
                          {data.job_title || data.job_role || 'Engineering Candidate'}
                        </span>
                      </div>

                      <div className={`mt-2.5 flex flex-wrap items-center gap-4 text-xs ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                        {candidate.email && (
                          <span className="flex items-center gap-1.5 font-medium">
                            <Mail className="h-3.5 w-3.5 text-slate-400" />
                            {candidate.email}
                          </span>
                        )}
                        {candidate.experience_years != null && (
                          <span className="flex items-center gap-1.5 font-medium">
                            <Briefcase className="h-3.5 w-3.5 text-slate-400" />
                            {candidate.experience_years} years experience
                          </span>
                        )}
                        <span className="flex items-center gap-1.5 font-medium">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {formatDate(interview.ended_at || interview.started_at)}
                        </span>
                        {interview.duration_minutes != null && (
                          <span className="flex items-center gap-1.5 font-medium">
                            <Clock className="h-3.5 w-3.5 text-slate-400" />
                            {interview.duration_minutes} min duration
                          </span>
                        )}
                      </div>

                      {/* Candidate Skills Tags */}
                      {candidate.skills && candidate.skills.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {candidate.skills.map((skill, idx) => (
                            <span
                              key={idx}
                              className={`rounded-md border px-2 py-0.5 text-[11px] font-medium ${
                                isLight
                                  ? 'border-slate-200 bg-slate-100 text-slate-700'
                                  : 'border-white/10 bg-slate-950/60 text-slate-300'
                              }`}
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Overall Score Highlight */}
                  {overallScore !== null && (
                    <div className={`flex items-center gap-4 rounded-2xl border p-4 shrink-0 shadow-xs ${
                      isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/60 border-white/10'
                    }`}>
                      <div className="text-right">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 block">
                          Overall Assessment
                        </span>
                        <span className={`text-xs font-bold ${
                          String(fitStatus).toLowerCase().includes('blacklisted')
                            ? 'text-rose-600 dark:text-rose-400'
                            : isLight ? 'text-indigo-700' : 'text-indigo-300'
                        }`}>{fitStatus}</span>
                      </div>
                      <div className={`flex h-14 w-14 items-center justify-center rounded-xl text-2xl font-black ${
                        String(fitStatus).toLowerCase().includes('blacklisted')
                          ? 'bg-rose-600 text-white shadow-xs'
                          : isLight
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'bg-indigo-500/20 text-indigo-300 border border-indigo-400/30'
                      }`}>
                        {Math.round(overallScore)}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Full Recruiter Report Viewer */}
              {recruiterReport ? (
                <RecruiterReportViewer
                  theme={theme}
                  report={recruiterReport}
                  sessionId={data.session_id || String(id)}
                />
              ) : (
                <div className={`rounded-2xl border p-12 text-center shadow-xs ${
                  isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10 backdrop-blur-md'
                }`}>
                  <AlertCircle className="mx-auto h-12 w-12 text-amber-500 mb-3" />
                  <h3 className={`text-base font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>Report Incomplete</h3>
                  <p className={`mt-1 text-sm ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                    This interview session has not been fully evaluated or ended yet.
                  </p>
                </div>
              )}
            </>
          ) : null}
        </main>
      </div>
    </>
  );
}
