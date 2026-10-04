import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import {
  ArrowLeft,
  Briefcase,
  CheckCircle2,
  Check,
  Code2,
  Clock,
  Sparkles,
  ArrowRight,
  Shield,
  Layers,
  AlertCircle,
  Share2,
  Compass,
} from 'lucide-react';

export default function JobDetailsPage() {
  const router = useRouter();
  const { id } = router.query;

  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isApplied, setIsApplied] = useState(false);

  useEffect(() => {
    if (!router.isReady || !id) return;
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();

    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('hiresight_applied_jobs');
      if (stored) {
        try {
          const ids = new Set(JSON.parse(stored));
          if (ids.has(id)) setIsApplied(true);
        } catch (e) {}
      }
    }
  }, [router.isReady, id]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        try {
          const profileData = await authService.getProfile();
          setProfile(profileData);
        } catch (pErr) {}
      } catch (userErr) {
        if (userErr?.response?.status === 401) {
          authService.logout();
          return;
        }
      }

      // Fetch single job with fallback
      try {
        const singleJob = await jobService.getJobPost(id);
        if (singleJob) {
          setJob(singleJob);
          return;
        }
      } catch {
        const allJobs = await jobService.getAllJobPosts();
        const found = (allJobs || []).find((j) => j.id === id);
        setJob(found || null);
      }
    } catch (err) {
      console.error('Failed to load job details:', err);
      if (err?.response?.status === 401) {
        authService.logout();
        return;
      }
      setError('Unable to load job details.');
    } finally {
      setLoading(false);
    }
  };

  const normalizeStringList = (val) => {
    if (val == null) return [];
    if (Array.isArray(val)) return val.map((s) => String(s).trim()).filter(Boolean);
    if (typeof val === 'string') {
      try {
        const p = JSON.parse(val);
        return Array.isArray(p) ? p.map((s) => String(s).trim()).filter(Boolean) : [];
      } catch {
        return [];
      }
    }
    return [];
  };

  const candidateSkills = useMemo(() => {
    if (!profile) return [];
    const base = normalizeStringList(profile.skills);
    const exp = normalizeStringList(profile.experienced_skills);
    const known = normalizeStringList(profile.known_skills);
    return Array.from(new Set([...base, ...exp, ...known]));
  }, [profile]);

  const candidateSkillSet = useMemo(() => {
    return new Set(candidateSkills.map((s) => s.toLowerCase()));
  }, [candidateSkills]);

  const requiredSkills = useMemo(() => {
    return normalizeStringList(job?.required_skills);
  }, [job]);

  const matchedSkills = useMemo(() => {
    return requiredSkills.filter((s) => candidateSkillSet.has(s.toLowerCase()));
  }, [requiredSkills, candidateSkillSet]);

  const missingSkills = useMemo(() => {
    return requiredSkills.filter((s) => !candidateSkillSet.has(s.toLowerCase()));
  }, [requiredSkills, candidateSkillSet]);

  const matchPercent = useMemo(() => {
    if (!requiredSkills.length) return 100;
    return Math.round((matchedSkills.length / requiredSkills.length) * 100);
  }, [matchedSkills, requiredSkills]);

  const handleApply = () => {
    if (!job?.id) return;
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('hiresight_applied_jobs');
      const set = stored ? new Set(JSON.parse(stored)) : new Set();
      set.add(job.id);
      localStorage.setItem('hiresight_applied_jobs', JSON.stringify(Array.from(set)));
      setIsApplied(true);
    }
    router.push(`/apply?jobId=${encodeURIComponent(job.id)}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-2 border-indigo-600/20 border-t-indigo-600" />
          <p className="text-xs font-medium text-slate-500">Loading role details…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-800 antialiased font-sans">
      <CandidateHeader activePath="/jobs" user={user} onLogout={authService.logout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
        {!job ? (
          <div className="rounded-2xl border border-slate-200/80 bg-white p-12 text-center shadow-xs">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-500 mb-3 border border-rose-100">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900">{error || 'Job not found'}</h2>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              This position may have been closed or removed by the hiring team.
            </p>
            <div className="mt-5 flex justify-center gap-3">
              {error && (
                <button
                  type="button"
                  onClick={loadData}
                  className="rounded-xl bg-blue-700 hover:bg-blue-800 px-4 py-2 text-xs font-semibold text-white shadow-xs"
                >
                  Retry
                </button>
              )}
              <button
                type="button"
                onClick={() => router.push('/jobs')}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs"
              >
                Back to Jobs
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Top Hero Card */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
              {/* Back breadcrumb */}
              <button
                type="button"
                onClick={() => router.push('/jobs')}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 mb-4 transition"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to all jobs
              </button>

              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="rounded-full bg-blue-50 border border-blue-200 text-blue-700 px-2.5 py-0.5 text-xs font-semibold">
                      {job.domain || 'Technology & Software'}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">Position ID: {job.id}</span>
                  </div>

                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                    {job.title}
                  </h1>
                </div>

                {/* Top Action Buttons */}
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => router.push('/jobs')}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                  >
                    All positions
                  </button>

                  {isApplied ? (
                    <button
                      type="button"
                      disabled
                      className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-50 border border-emerald-200 px-5 py-2.5 text-xs sm:text-sm font-semibold text-emerald-700"
                    >
                      <Check className="h-4 w-4" />
                      Applied
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleApply}
                      className="inline-flex items-center gap-2 rounded-xl bg-blue-700 hover:bg-blue-800 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white transition shadow-xs"
                    >
                      Apply and match
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* 2-Column Details Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column (8 cols): Description & Interview Format */}
              <div className="lg:col-span-8 space-y-6">
                {/* Role Overview */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
                  <h2 className="text-lg font-bold text-slate-900">Role Overview & Responsibilities</h2>
                  <div className="mt-4 prose prose-slate text-xs sm:text-sm leading-relaxed text-slate-600 whitespace-pre-wrap">
                    {job.description ||
                      'The employer has not provided a detailed markdown job description for this role yet. Please review the required competency skills on the right.'}
                  </div>
                </div>

                {/* Interview Structure Blueprint */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div>
                      <h2 className="text-lg font-bold text-slate-900">Assessment & Interview Blueprint</h2>
                      <p className="mt-1 text-xs sm:text-sm text-slate-500">
                        Rigorous, role-tailored AI evaluation calibrated across 6 sequential phases (22 questions total):
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/60">
                      22 Questions Paced
                    </span>
                  </div>

                  <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-blue-700 font-bold text-xs">
                          <Briefcase className="h-4 w-4" />
                          Phase 1: Introduction & CV
                        </div>
                        <span className="text-[11px] font-semibold text-blue-600 bg-blue-100/60 px-1.5 py-0.5 rounded">4 Qs</span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Career journey, motivations for the role, and project architectures extracted from your CV.
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-indigo-700 font-bold text-xs">
                          <Layers className="h-4 w-4" />
                          Phase 2: Core Technical
                        </div>
                        <span className="text-[11px] font-semibold text-indigo-600 bg-indigo-100/60 px-1.5 py-0.5 rounded">8 Qs</span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Required skills concepts in depth: runtime execution lifecycles, memory, concurrency, query optimization, and error handling.
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-cyan-700 font-bold text-xs">
                          <Sparkles className="h-4 w-4" />
                          Phase 3: System Design
                        </div>
                        <span className="text-[11px] font-semibold text-cyan-600 bg-cyan-100/60 px-1.5 py-0.5 rounded">3 Qs</span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Dedicated distributed architecture, microservices decoupling, caching, sharding, and scalability trade-offs.
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-violet-700 font-bold text-xs">
                          <Code2 className="h-4 w-4" />
                          Phase 4: Coding Sandbox
                        </div>
                        <span className="text-[11px] font-semibold text-violet-600 bg-violet-100/60 px-1.5 py-0.5 rounded">2 Qs</span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Monaco browser IDE execution tested against public & hidden test suites.
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-emerald-700 font-bold text-xs">
                          <Shield className="h-4 w-4" />
                          Phase 5: Behavioral
                        </div>
                        <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-100/60 px-1.5 py-0.5 rounded">3 Qs</span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Production outage triage, technical debt refactoring, and engineering team collaboration.
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-slate-700 font-bold text-xs">
                          <Compass className="h-4 w-4" />
                          Phase 6: Closing
                        </div>
                        <span className="text-[11px] font-semibold text-slate-600 bg-slate-200/60 px-1.5 py-0.5 rounded">2 Qs</span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Career growth alignment, team culture preferences, and candidate questions.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column (4 cols): Required Skills & Match Analysis */}
              <div className="lg:col-span-4 space-y-6">
                {/* Match Analysis Card */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-slate-900">Skill Match Analysis</h3>
                    <span className="text-xs font-bold text-blue-700 bg-blue-50 border border-blue-100 px-2.5 py-0.5 rounded-full">
                      {matchPercent}% match
                    </span>
                  </div>

                  <div className="mt-3">
                    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className="h-full bg-blue-700 rounded-full transition-all duration-500"
                        style={{ width: `${matchPercent}%` }}
                      />
                    </div>
                    <p className="mt-1.5 text-[11px] font-semibold text-slate-500">
                      {matchedSkills.length} of {requiredSkills.length} required skills on your profile
                    </p>
                  </div>

                  {/* Skills Cloud */}
                  <div className="mt-5 space-y-3">
                    {matchedSkills.length > 0 && (
                      <div>
                        <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider mb-2">
                          Matched on your Profile ({matchedSkills.length})
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {matchedSkills.map((sk, idx) => (
                            <span
                              key={`matched-${sk}-${idx}`}
                              className="rounded-lg bg-emerald-50 border border-emerald-200 px-2.5 py-1 text-xs font-medium text-emerald-800"
                            >
                              ✓ {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {missingSkills.length > 0 && (
                      <div className="pt-2">
                        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                          Skills to brush up on ({missingSkills.length})
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {missingSkills.map((sk, idx) => (
                            <span
                              key={`missing-${sk}-${idx}`}
                              className="rounded-lg bg-slate-50 border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600"
                            >
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Quick CTA */}
                  <div className="mt-6 pt-4 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={handleApply}
                      className="w-full rounded-xl bg-blue-700 hover:bg-blue-800 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition"
                    >
                      {isApplied ? 'Re-take / Continue Application' : 'Apply for this Position'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
