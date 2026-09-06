/**
 * Candidate Full Report Page (Issue 02 - Part 3)
 * Dynamic Route: /admin/candidates/[id]
 * Renders complete single-source-of-truth dossier for recruiter assessment & hiring decisions.
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
  Sparkles,
  Download,
  Share2,
  FileText,
  AlertCircle,
} from 'lucide-react';
import authService from '@/services/authService';
import adminDashboardService from '@/services/adminDashboardService';
import RecruiterReportViewer from '@/components/Interview/RecruiterReportViewer';

export default function CandidateReportPage() {
  const router = useRouter();
  const { id } = router.query;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);

  useEffect(() => {
    if (!router.isReady) return;
    if (!authService.isAuthenticated()) {
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

      <div className="min-h-screen bg-[#0B1120] text-slate-100 pb-16">
        {/* Sticky Top Header */}
        <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0B1120]/90 backdrop-blur-md px-4 py-3 sm:px-8">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/admin-dashboard"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/80 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-white/5 hover:text-white"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Dashboard</span>
              </Link>

              <div className="hidden sm:block">
                <span className="text-xs text-slate-500">/</span>
                <span className="ml-2 text-xs text-slate-400">Candidate Assessments</span>
                <span className="mx-2 text-xs text-slate-500">/</span>
                <span className="text-xs font-semibold text-white truncate max-w-xs">
                  {candidate.name || id}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleCopyShareLink}
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-slate-900/80 px-3.5 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-white/5 hover:text-white"
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
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-400/30 border-t-indigo-400" />
              <p className="text-sm text-slate-400">Loading comprehensive candidate dossier…</p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center max-w-2xl mx-auto space-y-4">
              <ShieldAlert className="mx-auto h-12 w-12 text-red-400" />
              <h2 className="text-lg font-bold text-white">Unable to Load Report</h2>
              <p className="text-sm text-red-200">{error}</p>
              <div className="pt-2 flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => id && loadReport(String(id))}
                  className="rounded-xl bg-red-500/20 px-4 py-2 text-xs font-semibold text-red-200 hover:bg-red-500/30"
                >
                  Retry
                </button>
                <Link
                  href="/admin-dashboard"
                  className="rounded-xl border border-white/15 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/5"
                >
                  Return to Dashboard
                </Link>
              </div>
            </div>
          ) : data ? (
            <>
              {/* Candidate Summary Header Hero Banner */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                  {/* Left: Avatar & Candidate Info */}
                  <div className="flex items-start gap-4">
                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-2xl font-black text-white shadow-lg shadow-indigo-500/20">
                      {(candidate.name || 'C').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h1 className="text-2xl font-bold text-white">{candidate.name}</h1>
                        <span className="rounded-full border border-indigo-400/40 bg-indigo-500/15 px-3 py-0.5 text-xs font-semibold text-indigo-300">
                          {data.job_title || data.job_role || 'Engineering Candidate'}
                        </span>
                      </div>

                      <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                        {candidate.email && (
                          <span className="flex items-center gap-1.5">
                            <Mail className="h-3.5 w-3.5 text-slate-500" />
                            {candidate.email}
                          </span>
                        )}
                        {candidate.experience_years != null && (
                          <span className="flex items-center gap-1.5">
                            <Briefcase className="h-3.5 w-3.5 text-slate-500" />
                            {candidate.experience_years} years experience
                          </span>
                        )}
                        <span className="flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 text-slate-500" />
                          {formatDate(interview.ended_at || interview.started_at)}
                        </span>
                        {interview.duration_minutes != null && (
                          <span className="flex items-center gap-1.5">
                            <Clock className="h-3.5 w-3.5 text-slate-500" />
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
                              className="rounded-md border border-white/10 bg-slate-950/60 px-2 py-0.5 text-[11px] font-medium text-slate-300"
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
                    <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4 shrink-0">
                      <div className="text-right">
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                          Overall Assessment
                        </span>
                        <span className="text-xs font-semibold text-indigo-300">{fitStatus}</span>
                      </div>
                      <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-indigo-500/20 text-2xl font-black text-indigo-300 border border-indigo-400/30">
                        {Math.round(overallScore)}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Full Recruiter Report Viewer (FEAT-009-FE) */}
              {recruiterReport ? (
                <RecruiterReportViewer
                  report={recruiterReport}
                  sessionId={data.session_id || String(id)}
                />
              ) : (
                <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-12 text-center backdrop-blur-md">
                  <AlertCircle className="mx-auto h-12 w-12 text-amber-400 mb-3" />
                  <h3 className="text-base font-semibold text-white">Report Incomplete</h3>
                  <p className="mt-1 text-sm text-slate-400">
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
