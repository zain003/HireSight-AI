import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import ResumeUpload from '@/components/Resume/ResumeUpload';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import {
  Briefcase,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Sparkles,
  Layers,
  Code2,
  Check,
  ChevronRight,
} from 'lucide-react';

export default function ApplyPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [notification, setNotification] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, []);

  useEffect(() => {
    if (!router.isReady || !jobs.length) return;
    const queryJobId = router.query.jobId;
    if (!queryJobId) return;
    const preselected = jobs.find((j) => j.id === queryJobId);
    if (preselected) setSelectedJob(preselected);
  }, [router.isReady, router.query.jobId, jobs]);

  const loadData = async () => {
    try {
      const [userData, jobsData] = await Promise.all([
        authService.getCurrentUser(),
        jobService.getAllJobPosts(),
      ]);
      setUser(userData);
      setJobs(jobsData || []);
    } catch (err) {
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const handleJobSelect = (e) => {
    const job = jobs.find((j) => j.id === e.target.value);
    setSelectedJob(job || null);
    setMatchResult(null);
    setNotification('');
  };

  const handleMatchResult = (result) => {
    setMatchResult(result);
    const percent = Number(result?.match_percent);
    if (!Number.isFinite(percent)) return;

    if (percent >= 50) {
      setNotification('You meet the baseline criteria for this position. Proceed to live AI interview setup.');
    } else {
      setNotification('Your skill match is below 50%. You may still practice or update your profile.');
    }
  };

  const handleStartInterview = () => {
    const jobId = selectedJob?.id;
    if (jobId) {
      router.push(`/interview-setup?jobPostId=${encodeURIComponent(jobId)}`);
    } else {
      router.push('/interview-setup');
    }
  };

  const matchPercent = Number(matchResult?.match_percent || 0);
  const matchedSkills = useMemo(() => matchResult?.matched_skills || [], [matchResult]);
  const missingSkills = useMemo(() => matchResult?.missing_skills || [], [matchResult]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-2 border-indigo-600/20 border-t-indigo-600" />
          <p className="text-xs font-medium text-slate-500">Loading application portal…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-800 antialiased font-sans">
      <CandidateHeader activePath="/apply" user={user} onLogout={authService.logout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
        {/* Top Header */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Apply & Match Skills
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
            Select an open role, upload your latest resume, and get instant skill alignment analysis before starting your live interview.
          </p>
        </div>

        {/* Notification Banner */}
        {notification && (
          <div className="flex items-center justify-between rounded-2xl border border-blue-200 bg-blue-50 p-4 text-xs font-semibold text-blue-900 shadow-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-blue-700 shrink-0" />
              <span>{notification}</span>
            </div>
            {matchPercent >= 50 && (
              <button
                type="button"
                onClick={handleStartInterview}
                className="rounded-xl bg-blue-700 hover:bg-blue-800 px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs"
              >
                Start Interview
              </button>
            )}
          </div>
        )}

        {/* Step 1: Choose Role Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Step 1</p>
          <h2 className="text-base font-bold text-slate-900 mb-3">Select Target Job Position</h2>

          <div className="relative">
            <select
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs sm:text-sm font-medium text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-2xs"
              value={selectedJob?.id || ''}
              onChange={handleJobSelect}
            >
              <option value="" disabled>
                Select an open position ({jobs.length} available)…
              </option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} — {job.domain || 'Engineering'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Step 2: Selected Job Overview Card */}
        {selectedJob && (
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Step 2</p>
                <h2 className="text-lg font-bold text-slate-900 mt-0.5">{selectedJob.title}</h2>
                <span className="mt-1 inline-block text-xs font-medium text-slate-500">
                  {selectedJob.domain || 'Technology & Engineering'}
                </span>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed line-clamp-3">
              {selectedJob.description || 'The employer has not added a detailed description yet.'}
            </p>

            {selectedJob.required_skills && selectedJob.required_skills.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Required Competencies
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {selectedJob.required_skills.map((skill, idx) => (
                    <span
                      key={`${skill}-${idx}`}
                      className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-700"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Resume Upload Dropzone */}
        {selectedJob && (
          <div>
            <ResumeUpload
              selectedJob={selectedJob}
              onMatchResult={handleMatchResult}
              onUploadSuccess={() => {}}
            />
          </div>
        )}

        {/* Step 4: Match Breakdown Result Card */}
        {matchResult && (
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Skill Alignment Summary</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Comparison between your uploaded CV and the requirements for {selectedJob?.title}.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Overall Match</p>
                  <p className="text-xl font-extrabold text-blue-700">{matchPercent}%</p>
                </div>
                <button
                  type="button"
                  onClick={handleStartInterview}
                  className="rounded-xl bg-blue-700 hover:bg-blue-800 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition"
                >
                  Proceed to Live Interview
                </button>
              </div>
            </div>

            {/* Skills breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-4 border-t border-slate-100">
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
                <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Matched Skills ({matchedSkills.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {matchedSkills.length === 0 ? (
                    <span className="text-xs text-slate-400 italic">No direct matches found.</span>
                  ) : (
                    matchedSkills.map((sk, idx) => (
                      <span
                        key={`matched-${sk}-${idx}`}
                        className="rounded-lg bg-white border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 shadow-2xs"
                      >
                        ✓ {sk}
                      </span>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
                  Skills to Brush Up On ({missingSkills.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {missingSkills.length === 0 ? (
                    <span className="text-xs text-slate-400 italic">All required skills matched!</span>
                  ) : (
                    missingSkills.map((sk, idx) => (
                      <span
                        key={`missing-${sk}-${idx}`}
                        className="rounded-lg bg-white border border-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-600 shadow-2xs"
                      >
                        {sk}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
