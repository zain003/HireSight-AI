import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';

export default function JobsPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

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

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-300">Loading jobs...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      <CandidateHeader activePath="/jobs" user={user} onLogout={authService.logout} />
      <main className="container mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Active jobs</h1>
          <p className="mt-1 text-sm text-slate-300">Browse available positions and review role requirements.</p>
        </div>

        {jobs.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-8 text-center text-sm text-slate-300 shadow-sm">
            No active jobs right now.
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <div key={job.id} className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-white">{job.title}</h2>
                    {job.domain && (
                      <p className="mt-1 text-xs uppercase tracking-[0.12em] text-slate-400">{job.domain}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => router.push(`/jobs/${encodeURIComponent(job.id)}`)}
                      className="rounded-lg border border-white/20 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-white/10"
                    >
                      View
                    </button>
                    <button
                      onClick={() => router.push(`/apply?jobId=${encodeURIComponent(job.id)}`)}
                      className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                    >
                      Apply
                    </button>
                  </div>
                </div>

                <p className="mt-3 text-sm leading-relaxed text-slate-300">
                  {job.description || 'No job description provided.'}
                </p>

                <div className="mt-4">
                  <p className="mb-2 text-xs uppercase tracking-[0.12em] text-slate-400">Required skills</p>
                  <div className="flex flex-wrap gap-2">
                    {(job.required_skills || []).map((skill, idx) => (
                      <span key={`${skill}-${idx}`} className="rounded-md border border-white/15 bg-white/10 px-2.5 py-1 text-xs text-slate-200">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
