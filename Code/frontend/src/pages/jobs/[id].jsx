import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';

export default function JobDetailsPage() {
  const router = useRouter();
  const { id } = router.query;

  const [user, setUser] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!router.isReady) return;
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router.isReady]);

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

  const job = useMemo(() => jobs.find((j) => j.id === id), [jobs, id]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-300">Loading job details...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      <CandidateHeader activePath="/jobs" user={user} onLogout={authService.logout} />
      <main className="container mx-auto space-y-6 px-6 py-8">
        {!job ? (
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-8 text-center text-slate-300">
            <p>Job not found.</p>
            <button
              onClick={() => router.push('/jobs')}
              className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
            >
              Back to Jobs
            </button>
          </div>
        ) : (
          <>
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Job details</p>
                  <h1 className="mt-1 text-2xl font-bold text-white">{job.title}</h1>
                  {job.domain && (
                    <p className="mt-2 text-sm font-medium text-indigo-300">{job.domain}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => router.push('/jobs')}
                    className="rounded-lg border border-white/20 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-white/10"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => router.push(`/apply?jobId=${encodeURIComponent(job.id)}`)}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                  >
                    Apply Now
                  </button>
                </div>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
              <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-white">Role overview</h2>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                  {job.description || 'No description provided for this role.'}
                </p>
              </section>

              <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-white">Required skills</h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {(job.required_skills || []).length ? (
                    job.required_skills.map((skill, idx) => (
                      <span
                        key={`${skill}-${idx}`}
                        className="rounded-md border border-white/15 bg-white/10 px-2.5 py-1 text-xs text-slate-200"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">No required skills listed.</p>
                  )}
                </div>
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
