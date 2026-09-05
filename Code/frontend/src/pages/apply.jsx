import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import ResumeUpload from '@/components/Resume/ResumeUpload';
import CandidateHeader from '@/components/Candidate/CandidateHeader';

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
  }, [router]);

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

    if (percent >= 80) {
      setNotification('You are eligible for the interview test. Click "Start Interview" to continue.');
    } else {
      setNotification('You do not meet the criteria for this job. Better luck next time!');
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

  const handleUploadSuccess = async () => {
    setNotification('Resume parsed and profile updated!');
  };

  const matchPercent = Number(matchResult?.match_percent || 0);
  const matchedSkills = useMemo(() => matchResult?.matched_skills || [], [matchResult]);
  const missingSkills = useMemo(() => matchResult?.missing_skills || [], [matchResult]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-300">Loading apply page...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      <CandidateHeader activePath="/apply" user={user} onLogout={authService.logout} />
      <main className="container mx-auto space-y-6 px-6 py-8">
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-white">Apply for jobs</h1>
          <p className="mt-1 text-sm text-slate-300">
            Select a role, upload your resume, and get AI-powered skill match analysis.
          </p>
        </div>

        {notification && (
          <div className="rounded-xl border border-indigo-400/30 bg-indigo-500/10 px-4 py-3 text-sm text-indigo-200">
            {notification}
          </div>
        )}

        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-400">Step 1</p>
          <h2 className="mt-1 text-base font-semibold text-white">Choose a job post</h2>
          <label className="mb-1 mt-3 block text-sm font-medium text-slate-300">Job</label>
          <select
            className="w-full rounded-lg border border-white/15 bg-slate-950/50 px-3 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            value={selectedJob?.id || ''}
            onChange={handleJobSelect}
          >
            <option value="" disabled>Select a job...</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </div>

        {selectedJob && (
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
            <p className="text-xs uppercase tracking-[0.12em] text-slate-400">Step 2</p>
            <h2 className="mt-1 text-base font-semibold text-white">{selectedJob.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              {selectedJob.description || 'No description available.'}
            </p>
            <div className="mt-4">
              <p className="mb-2 text-xs uppercase tracking-[0.12em] text-slate-400">Required skills</p>
              <div className="flex flex-wrap gap-2">
                {(selectedJob.required_skills || []).map((skill, idx) => (
                  <span key={`${skill}-${idx}`} className="rounded-md border border-white/15 bg-white/10 px-2.5 py-1 text-xs text-slate-200">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        <div>
          <p className="mb-2 px-1 text-xs uppercase tracking-[0.12em] text-slate-500">Step 3</p>
          <ResumeUpload
            selectedJob={selectedJob}
            onUploadSuccess={handleUploadSuccess}
            onMatchResult={handleMatchResult}
          />
        </div>

        {!selectedJob && (
          <p className="rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3 text-sm text-slate-300 shadow-sm">
            Select a job first, then upload your resume for matching.
          </p>
        )}

        {matchResult && (
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.12em] text-slate-400">Match result</p>
                <h3 className="mt-1 text-base font-semibold text-white">Role fit analysis</h3>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-white">{matchPercent}%</p>
                <p className="text-xs text-slate-400">overall match</p>
              </div>
            </div>

            <div className="mt-4">
              <div className="h-3 overflow-hidden rounded-full bg-slate-700">
                <div
                  className={`h-full ${
                    matchPercent >= 70 ? 'bg-emerald-500' : matchPercent >= 50 ? 'bg-amber-400' : 'bg-red-500'
                  }`}
                  style={{ width: `${matchPercent}%` }}
                />
              </div>
              <p className={`mt-2 text-sm font-medium ${matchPercent >= 80 ? 'text-emerald-300' : 'text-red-300'}`}>
                {matchPercent >= 80 ? 'Eligible for interview' : 'Below eligibility threshold (80%)'}
              </p>

              {matchPercent >= 80 && (
                <button
                  onClick={handleStartInterview}
                  className="mt-3 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600"
                >
                  Start Interview
                </button>
              )}
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <p className="mb-2 text-xs uppercase tracking-[0.12em] text-slate-400">Matched skills</p>
                <div className="flex flex-wrap gap-2">
                  {matchedSkills.slice(0, 10).map((skill, idx) => (
                    <span key={`${skill}-${idx}`} className="rounded-md border border-emerald-300/50 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-300">
                      {skill}
                    </span>
                  ))}
                  {matchedSkills.length > 10 && (
                    <span className="rounded-md border border-emerald-300/50 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-300">
                      +{matchedSkills.length - 10} more
                    </span>
                  )}
                </div>
              </div>
              <div>
                <p className="mb-2 text-xs uppercase tracking-[0.12em] text-slate-400">Missing skills</p>
                <div className="flex flex-wrap gap-2">
                  {missingSkills.slice(0, 8).map((skill, idx) => (
                    <span key={`${skill}-${idx}`} className="rounded-md border border-red-300/50 bg-red-500/10 px-2.5 py-1 text-xs text-red-300">
                      {skill}
                    </span>
                  ))}
                  {missingSkills.length > 8 && (
                    <span className="rounded-md border border-red-300/50 bg-red-500/10 px-2.5 py-1 text-xs text-red-300">
                      +{missingSkills.length - 8} more
                    </span>
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
