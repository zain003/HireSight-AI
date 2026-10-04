import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import {
  Briefcase,
  Search,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  ExternalLink,
  Layers,
  Check,
  AlertCircle,
  RefreshCw,
  Filter,
} from 'lucide-react';

export default function JobsPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [appliedJobIds, setAppliedJobIds] = useState(new Set());

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();

    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('hiresight_applied_jobs');
      if (stored) {
        try {
          setAppliedJobIds(new Set(JSON.parse(stored)));
        } catch (e) {}
      }
    }
  }, []);

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

      const jobsData = await jobService.getAllJobPosts();
      setJobs(jobsData || []);
    } catch (err) {
      console.error('Failed to load active jobs:', err);
      if (err?.response?.status === 401) {
        authService.logout();
        return;
      }
      setError('Unable to load jobs at this moment. Please check your connection and try again.');
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const normalizeStringList = (val) => {
    if (val == null) return [];
    if (Array.isArray(val)) {
      return val.map((s) => String(s).trim()).filter(Boolean);
    }
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

  // Derive categories
  const categories = useMemo(() => {
    const defaultPills = ['All', 'Best matches', 'Cloud', 'Backend', 'Full stack', 'Security', 'Data'];
    const dynamicDomains = Array.from(
      new Set(
        jobs
          .map((j) => j.domain)
          .filter(Boolean)
          .map((d) => d.trim())
      )
    );
    return Array.from(new Set([...defaultPills, ...dynamicDomains]));
  }, [jobs]);

  // Process jobs with matching metrics
  const processedJobs = useMemo(() => {
    return jobs.map((job) => {
      const reqSkills = normalizeStringList(job.required_skills);
      const matched = reqSkills.filter((s) => candidateSkillSet.has(s.toLowerCase()));
      const matchedCount = matched.length;
      const totalCount = reqSkills.length || 1;
      const matchRatio = matchedCount / totalCount;

      let matchTier = 'Good match';
      let matchTierClass = 'bg-amber-50 text-amber-700 border-amber-200/80';

      if (matchRatio >= 0.5 || matchedCount >= 4) {
        matchTier = 'Strong match';
        matchTierClass = 'bg-emerald-50 text-emerald-700 border-emerald-200/80';
      }

      return {
        ...job,
        required_skills: reqSkills,
        matchedSkills: matched,
        matchedSkillsCount: matchedCount,
        totalSkillsCount: totalCount,
        matchTier,
        matchTierClass,
        matchRatio,
      };
    });
  }, [jobs, candidateSkillSet]);

  const filteredJobs = useMemo(() => {
    return processedJobs.filter((job) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = job.title?.toLowerCase().includes(q);
        const matchesDomain = job.domain?.toLowerCase().includes(q);
        const matchesDesc = job.description?.toLowerCase().includes(q);
        const matchesSkill = job.required_skills?.some((s) => s.toLowerCase().includes(q));
        if (!matchesTitle && !matchesDomain && !matchesDesc && !matchesSkill) {
          return false;
        }
      }

      // 2. Category Filter
      if (selectedCategory === 'All') return true;
      if (selectedCategory === 'Best matches') return job.matchTier === 'Strong match';
      if (job.domain?.toLowerCase().includes(selectedCategory.toLowerCase())) return true;
      if (job.title?.toLowerCase().includes(selectedCategory.toLowerCase())) return true;
      return false;
    });
  }, [processedJobs, searchQuery, selectedCategory]);

  const handleApplyClick = (jobId) => {
    const updated = new Set(appliedJobIds);
    updated.add(jobId);
    setAppliedJobIds(updated);
    if (typeof window !== 'undefined') {
      localStorage.setItem('hiresight_applied_jobs', JSON.stringify(Array.from(updated)));
    }
    router.push(`/apply?jobId=${encodeURIComponent(jobId)}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-2 border-indigo-600/20 border-t-indigo-600" />
          <p className="text-xs font-medium text-slate-500">Loading active opportunities…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-800 antialiased font-sans">
      <CandidateHeader activePath="/jobs" user={user} onLogout={authService.logout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
        {/* Top Header Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                Active Job Openings
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
                Explore open positions, review required technical competencies, and apply directly with your saved resume or profile.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-1.5 text-xs font-bold text-slate-700 shadow-2xs">
                {jobs.length} total roles available
              </span>
            </div>
          </div>

          {/* Search & Filter Bar */}
          <div className="mt-6 pt-6 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            {/* Category Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {categories.map((cat) => {
                const active = selectedCategory.toLowerCase() === cat.toLowerCase();
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSelectedCategory(cat)}
                    className={`shrink-0 rounded-full px-3.5 py-1 text-xs font-semibold transition-all ${
                      active
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'bg-white border border-slate-200/80 text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>

            {/* Search Input */}
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by role or skill…"
                className="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-2xs"
              />
            </div>
          </div>
        </div>

        {/* Error Notice */}
        {error && (
          <div className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 shadow-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={loadData}
              className="rounded-xl border border-rose-200 bg-white px-3 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition shadow-2xs"
            >
              Retry
            </button>
          </div>
        )}

        {/* Job Cards 2-Column Grid */}
        {filteredJobs.length === 0 && !error ? (
          <div className="rounded-2xl border border-slate-200/80 bg-white p-12 text-center shadow-xs">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 text-slate-400 mb-3 border border-slate-200/80">
              <Briefcase className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">No matching positions found</h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              We couldn't find any job posts matching "{searchQuery || selectedCategory}". Try clearing your filters.
            </p>
            <button
              type="button"
              onClick={() => {
                setSelectedCategory('All');
                setSearchQuery('');
              }}
              className="mt-4 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition"
            >
              Reset all filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredJobs.map((job) => {
              const isApplied = appliedJobIds.has(job.id);
              return (
                <div
                  key={job.id}
                  className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs hover:shadow-sm hover:border-slate-300 transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Header: Title, Domain, Match Tier Badge */}
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="text-lg font-bold text-slate-900">{job.title}</h2>
                        <span className="mt-1 inline-block text-xs font-medium text-slate-500">
                          {job.domain || 'Technology & Engineering'}
                        </span>
                      </div>
                      <span
                        className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${job.matchTierClass}`}
                      >
                        {job.matchTier}
                      </span>
                    </div>

                    {/* Description */}
                    <p className="mt-3 text-xs sm:text-sm text-slate-600 leading-relaxed line-clamp-3">
                      {job.description || 'The employer has not added a detailed description yet.'}
                    </p>

                    {/* Required Skills with Match Highlights */}
                    {job.required_skills && job.required_skills.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                          Required Competencies
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {job.required_skills.slice(0, 6).map((sk, idx) => {
                            const isMatched = candidateSkillSet.has(sk.toLowerCase());
                            return (
                              <span
                                key={`${sk}-${idx}`}
                                className={`rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
                                  isMatched
                                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                                    : 'bg-slate-50 border-slate-200 text-slate-700'
                                }`}
                              >
                                {isMatched && '✓ '}
                                {sk}
                              </span>
                            );
                          })}
                          {job.required_skills.length > 6 && (
                            <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-500">
                              +{job.required_skills.length - 6} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer Row: Skill Match ratio & CTA Buttons */}
                  <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                    <span className="text-xs font-medium text-slate-500">
                      {job.matchedSkillsCount} of {job.totalSkillsCount} skills matched
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => router.push(`/jobs/${encodeURIComponent(job.id)}`)}
                        className="rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                      >
                        Details
                      </button>

                      {isApplied ? (
                        <button
                          type="button"
                          disabled
                          className="inline-flex items-center gap-1 rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-2 text-xs font-semibold text-emerald-700"
                        >
                          <Check className="h-3.5 w-3.5" />
                          Applied
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleApplyClick(job.id)}
                          className="rounded-xl bg-blue-700 hover:bg-blue-800 px-4 py-2 text-xs font-semibold text-white transition shadow-xs"
                        >
                          Apply and match
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
