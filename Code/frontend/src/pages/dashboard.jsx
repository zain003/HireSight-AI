/**
 * HireSight Candidate Dashboard
 * Matches modern clean SaaS aesthetics with complete functional fidelity.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import resumeService from '@/services/resumeService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import {
  ArrowRight,
  CheckCircle2,
  Circle,
  Search,
  Upload,
  Video,
  Sun,
  Home,
  Headphones,
  Check,
  Briefcase,
  Layers,
  Sparkles,
  Shield,
  HelpCircle,
  AlertTriangle,
  Clock,
  Mic,
  X,
  FileText,
} from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [jobPosts, setJobPosts] = useState([]);
  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeGuideTab, setActiveGuideTab] = useState('camera');
  const [uploadingResume, setUploadingResume] = useState(false);
  const [uploadNotice, setUploadNotice] = useState(null);
  const [appliedJobs, setAppliedJobs] = useState(new Set());

  // Camera & Mic Quick Test Modal state
  const [isTestingMedia, setIsTestingMedia] = useState(false);
  const [cameraTested, setCameraTested] = useState(false);
  const [mediaStream, setMediaStream] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const videoRef = useRef(null);
  const audioContextRef = useRef(null);
  const animFrameRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadUserData();
    loadJobPosts();

    // Check if camera was previously tested
    if (typeof window !== 'undefined') {
      const storedTest = localStorage.getItem('hiresight_camera_tested');
      if (storedTest === 'true') {
        setCameraTested(true);
      }
      const storedApplied = localStorage.getItem('hiresight_applied_jobs');
      if (storedApplied) {
        try {
          setAppliedJobs(new Set(JSON.parse(storedApplied)));
        } catch (e) {}
      }
    }
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
      try {
        const profileData = await authService.getProfile();
        setProfile(profileData);
      } catch (err) {
        console.log('No profile found');
      }
    } catch (err) {
      console.error('Failed to load user data:', err);
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const loadJobPosts = async () => {
    try {
      const posts = await jobService.getAllJobPosts();
      setJobPosts(posts || []);
    } catch (err) {
      console.error('Failed to load job posts:', err);
    }
  };

  const handleLogout = () => authService.logout();

  /** Normalize array or json strings */
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

  const skills = useMemo(() => {
    if (!profile) return [];
    const base = normalizeStringList(profile.skills);
    const exp = normalizeStringList(profile.experienced_skills);
    const known = normalizeStringList(profile.known_skills);
    return Array.from(new Set([...base, ...exp, ...known]));
  }, [profile]);

  const topRole = useMemo(() => {
    if (!profile) return 'Software Engineer';
    if (profile.job_role && profile.job_role.trim()) return profile.job_role.trim();
    const titles = normalizeStringList(profile.job_titles);
    if (titles.length > 0) return titles[0];
    return 'DevOps';
  }, [profile]);

  const hasResume = Boolean(profile?.resume_path || skills.length > 0);

  // Derive categories for filter pills
  const categories = useMemo(() => {
    const defaultPills = ['All', 'Best matches', 'Cloud', 'Backend', 'Full stack', 'Security', 'Data'];
    const dynamicDomains = Array.from(
      new Set(
        jobPosts
          .map((j) => j.domain)
          .filter(Boolean)
          .map((d) => d.trim())
      )
    );
    const set = new Set([...defaultPills, ...dynamicDomains]);
    return Array.from(set);
  }, [jobPosts]);

  // Calculate matching score and filter jobs
  const processedJobs = useMemo(() => {
    const candidateSkillSet = new Set(skills.map((s) => s.toLowerCase()));

    return jobPosts.map((job) => {
      const reqSkills = normalizeStringList(job.required_skills);
      const matched = reqSkills.filter((s) => candidateSkillSet.has(s.toLowerCase()));
      const matchCount = matched.length;
      const totalCount = reqSkills.length || 1;
      const matchRatio = matchCount / totalCount;

      let matchTier = 'Good match';
      let matchTierClass = 'bg-amber-50 text-amber-700 border-amber-200/80';

      if (matchRatio >= 0.5 || matchCount >= 4 || (job.title && job.title.toLowerCase().includes(topRole.toLowerCase()))) {
        matchTier = 'Strong match';
        matchTierClass = 'bg-emerald-50 text-emerald-700 border-emerald-200/80';
      }

      return {
        ...job,
        required_skills: reqSkills,
        matchedSkillsCount: matchCount,
        totalSkillsCount: totalCount,
        matchTier,
        matchTierClass,
        matchRatio,
      };
    });
  }, [jobPosts, skills, topRole]);

  const filteredJobs = useMemo(() => {
    return processedJobs.filter((job) => {
      // 1. Search filter
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

      // 2. Category filter
      if (activeCategory === 'All') return true;
      if (activeCategory === 'Best matches') return job.matchTier === 'Strong match';
      if (job.domain?.toLowerCase().includes(activeCategory.toLowerCase())) return true;
      if (job.title?.toLowerCase().includes(activeCategory.toLowerCase())) return true;
      return false;
    });
  }, [processedJobs, searchQuery, activeCategory]);

  // Readiness steps calculation
  const readinessSteps = useMemo(() => {
    const s1 = hasResume;
    const s2 = skills.length > 0;
    const s3 = cameraTested;
    const s4 = appliedJobs.size > 0 || Boolean(profile?.job_role);
    const count = [s1, s2, s3, s4].filter(Boolean).length;
    return {
      step1: s1,
      step2: s2,
      step3: s3,
      step4: s4,
      completedCount: count,
      progressPct: Math.round((count / 4) * 100),
    };
  }, [hasResume, skills.length, cameraTested, appliedJobs.size, profile?.job_role]);

  // Handle Quick Resume Upload
  const handleResumeFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingResume(true);
    setUploadNotice({ type: 'info', message: 'Analyzing resume and extracting technical skills...' });
    try {
      const parsed = await resumeService.uploadResume(file);
      await loadUserData();
      setUploadNotice({
        type: 'success',
        message: `Resume uploaded successfully! Found ${parsed?.skills?.length || 0} skills.`,
      });
      setTimeout(() => setUploadNotice(null), 4000);
    } catch (err) {
      console.error('Resume upload failed:', err);
      setUploadNotice({
        type: 'error',
        message: 'Could not parse resume. Please try uploading via the Profile page.',
      });
      setTimeout(() => setUploadNotice(null), 4000);
    } finally {
      setUploadingResume(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Start Camera & Microphone Test
  const startMediaTest = async () => {
    setIsTestingMedia(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
        audio: true,
      });
      setMediaStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }

      // Audio Level meter
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx && stream.getAudioTracks().length > 0) {
        const audioCtx = new AudioCtx();
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);
        audioContextRef.current = audioCtx;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const updateAudio = () => {
          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          const avg = sum / dataArray.length;
          setAudioLevel(Math.min(100, Math.round(avg * 2.5)));
          animFrameRef.current = requestAnimationFrame(updateAudio);
        };
        updateAudio();
      }
    } catch (err) {
      console.error('Failed to access media devices:', err);
    }
  };

  const stopMediaTest = (markCompleted = false) => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
      setMediaStream(null);
    }
    if (markCompleted) {
      setCameraTested(true);
      if (typeof window !== 'undefined') {
        localStorage.setItem('hiresight_camera_tested', 'true');
      }
    }
    setIsTestingMedia(false);
  };

  const handleApplyClick = (jobId) => {
    const updated = new Set(appliedJobs);
    updated.add(jobId);
    setAppliedJobs(updated);
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
          <p className="text-xs font-medium text-slate-500">Loading your candidate portal…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-800 antialiased font-sans">
      <CandidateHeader activePath="/dashboard" user={user} onLogout={handleLogout} />

      {/* Hidden resume input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        onChange={handleResumeFileSelect}
        className="hidden"
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
        {/* Upload Status Toast / Notice */}
        {uploadNotice && (
          <div
            className={`flex items-center justify-between rounded-xl px-4 py-3 text-xs font-medium border shadow-xs transition-all ${
              uploadNotice.type === 'error'
                ? 'bg-rose-50 border-rose-200 text-rose-800'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800'
            }`}
          >
            <span>{uploadNotice.message}</span>
            <button onClick={() => setUploadNotice(null)} className="text-slate-400 hover:text-slate-600">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* SECTION 1: HERO & INTERVIEW READINESS (2 COLUMNS)                          */}
        {/* ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Main Card: Welcome & Stats */}
          <div className="lg:col-span-8 rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs flex flex-col justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                Welcome back, <span className="text-slate-900">{user?.username || 'Candidate'}</span>
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl">
                Your resume is ready and matched to open roles. Pick a role, check your setup, and start your interview when you feel prepared.
              </p>

              {/* Action Buttons */}
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => router.push('/interview-setup')}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-700 hover:bg-blue-800 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-all"
                >
                  Configure and start interview
                  <ArrowRight className="h-4 w-4" />
                </button>

                <button
                  type="button"
                  disabled={uploadingResume}
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs disabled:opacity-60"
                >
                  {uploadingResume ? 'Uploading…' : 'Upload new resume'}
                </button>
              </div>
            </div>

            {/* Bottom 3 Stat Mini-Columns */}
            <div className="mt-8 pt-6 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-4">
              {/* Stat 1: Profile */}
              <div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Profile</p>
                <div className="mt-1 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span className="text-sm font-bold text-slate-900">
                    {hasResume ? 'Resume on file' : 'Profile ready'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {skills.length > 0 ? `${skills.length} skills extracted` : 'Setup your technical skills'}
                </p>
              </div>

              {/* Stat 2: Open Positions */}
              <div className="sm:border-l sm:border-slate-100 sm:pl-5">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Open positions</p>
                <div className="mt-1">
                  <span className="text-xl font-extrabold text-slate-900">{jobPosts.length || 10}</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const el = document.getElementById('open-positions-section');
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="text-[11px] font-semibold text-blue-700 hover:text-blue-800 hover:underline"
                >
                  Browse roles
                </button>
              </div>

              {/* Stat 3: Best Match */}
              <div className="sm:border-l sm:border-slate-100 sm:pl-5">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Best match</p>
                <div className="mt-1">
                  <span className="text-sm font-bold text-slate-900 truncate block">{topRole}</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Based on your skills</p>
              </div>
            </div>
          </div>

          {/* Right Card: Interview Readiness */}
          <div className="lg:col-span-4 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs flex flex-col justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Interview readiness</h2>
              <p className="mt-0.5 text-xs text-slate-500">Finish these steps for the smoothest start.</p>

              {/* Progress bar */}
              <div className="mt-4">
                <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-emerald-600 rounded-full transition-all duration-500"
                    style={{ width: `${readinessSteps.progressPct}%` }}
                  />
                </div>
                <p className="mt-1.5 text-[11px] font-semibold text-slate-500">
                  {readinessSteps.completedCount} of 4 steps done
                </p>
              </div>

              {/* 4 Steps Checklist */}
              <div className="mt-4 divide-y divide-slate-100">
                {/* Step 1 */}
                <div className="py-2.5 flex items-center justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    {readinessSteps.step1 ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-300 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="text-xs font-semibold text-slate-800">Resume uploaded</p>
                      <p className="text-[11px] text-slate-500">{skills.length} skills found</p>
                    </div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="py-2.5 flex items-center justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    {readinessSteps.step2 ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-300 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="text-xs font-semibold text-slate-800">Skills matched to roles</p>
                      <p className="text-[11px] text-slate-500">Best match: {topRole}</p>
                    </div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="py-2.5 flex items-center justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    {readinessSteps.step3 ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="text-xs font-semibold text-slate-800">Camera and microphone</p>
                      <p className="text-[11px] text-slate-500">Takes about 10 seconds</p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={startMediaTest}
                    className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                  >
                    {cameraTested ? 'Re-test' : 'Test now'}
                  </button>
                </div>

                {/* Step 4 */}
                <div className="py-2.5 flex items-center justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    {readinessSteps.step4 ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-300 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="text-xs font-semibold text-slate-800">Choose a role</p>
                      <p className="text-[11px] text-slate-500">
                        {appliedJobs.size > 0 ? 'Applied' : 'Select a target position'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* SECTION 2: OPEN POSITIONS                                                 */}
        {/* ========================================================================= */}
        <section id="open-positions-section" className="space-y-4 pt-2">
          {/* Section Header */}
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900">Open positions</h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                Apply with your saved resume. We match your skills to each role.
              </p>
            </div>

            {/* Search Input & Show All */}
            <div className="flex items-center gap-2.5 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search roles or skills"
                  className="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 shadow-2xs"
                />
              </div>

              <button
                type="button"
                onClick={() => {
                  setActiveCategory('All');
                  setSearchQuery('');
                }}
                className="shrink-0 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
              >
                Show all {jobPosts.length}
              </button>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {categories.map((cat) => {
              const active = activeCategory.toLowerCase() === cat.toLowerCase();
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setActiveCategory(cat)}
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

          {/* Job Cards 2-Column Grid */}
          {filteredJobs.length === 0 ? (
            <div className="rounded-2xl border border-slate-200/80 bg-white p-8 text-center text-sm text-slate-500 shadow-xs">
              No matching positions found. Try selecting "All" or resetting your search.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredJobs.map((job) => {
                const isApplied = appliedJobs.has(job.id);
                return (
                  <div
                    key={job.id}
                    className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs hover:shadow-sm hover:border-slate-300 transition-all flex flex-col justify-between"
                  >
                    <div>
                      {/* Top Header: Title, Domain, Match Badge */}
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="text-base font-bold text-slate-900">{job.title}</h3>
                          <p className="text-xs text-slate-500 font-medium mt-0.5">{job.domain || 'Technology'}</p>
                        </div>
                        <span
                          className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${job.matchTierClass}`}
                        >
                          {job.matchTier}
                        </span>
                      </div>

                      {/* Description Snippet */}
                      <p className="mt-2.5 text-xs text-slate-600 leading-relaxed line-clamp-2">
                        {job.description || 'The employer has not added a description yet.'}
                      </p>

                      {/* Skill Tags */}
                      {job.required_skills && job.required_skills.length > 0 && (
                        <div className="mt-3.5 flex flex-wrap gap-1.5">
                          {job.required_skills.slice(0, 4).map((sk, idx) => (
                            <span
                              key={`${sk}-${idx}`}
                              className="rounded-lg border border-slate-200 bg-slate-50/80 px-2.5 py-0.5 text-[11px] font-medium text-slate-700"
                            >
                              {sk}
                            </span>
                          ))}
                          {job.required_skills.length > 4 && (
                            <span className="rounded-lg border border-slate-200 bg-slate-50/80 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                              +{job.required_skills.length - 4} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Footer Row: Match Ratio & Action Buttons */}
                    <div className="mt-4 pt-3.5 border-t border-slate-100 flex items-center justify-between gap-2">
                      <span className="text-xs font-medium text-slate-500">
                        {job.matchedSkillsCount} of {job.totalSkillsCount} skills match
                      </span>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => router.push('/jobs')}
                          className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                        >
                          Details
                        </button>

                        {isApplied ? (
                          <button
                            type="button"
                            disabled
                            className="inline-flex items-center gap-1 rounded-xl bg-emerald-50 border border-emerald-200 px-3.5 py-1.5 text-xs font-semibold text-emerald-700"
                          >
                            <Check className="h-3.5 w-3.5" />
                            Applied
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleApplyClick(job.id)}
                            className="rounded-xl bg-blue-700 hover:bg-blue-800 px-3.5 py-1.5 text-xs font-semibold text-white transition shadow-xs"
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
        </section>

        {/* ========================================================================= */}
        {/* SECTION 3: INTERVIEW PREPARATION GUIDE (TABBED INTERFACE)                   */}
        {/* ========================================================================= */}
        <section className="space-y-4 pt-2">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">Interview preparation guide</h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Four short guides to help you feel confident before you start.
            </p>
          </div>

          {/* 2-Column Tabbed Guide Container */}
          <div className="rounded-2xl border border-slate-200/80 bg-white shadow-xs overflow-hidden grid grid-cols-1 md:grid-cols-12">
            {/* Left Sidebar of 4 Tabs */}
            <div className="md:col-span-4 border-b md:border-b-0 md:border-r border-slate-100 bg-slate-50/50 p-3 space-y-1.5">
              {/* Tab 1 */}
              <button
                type="button"
                onClick={() => setActiveGuideTab('camera')}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  activeGuideTab === 'camera'
                    ? 'bg-white border border-slate-200/90 shadow-2xs'
                    : 'border border-transparent hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs sm:text-sm font-bold text-slate-900">Camera and setup</p>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-md bg-blue-50 text-blue-700 border border-blue-200/70 px-1.5 py-0.5 text-[10px] font-semibold">
                    Essential
                  </span>
                  <span className="text-[11px] text-slate-400">2 min</span>
                </div>
              </button>

              {/* Tab 2 */}
              <button
                type="button"
                onClick={() => setActiveGuideTab('star')}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  activeGuideTab === 'star'
                    ? 'bg-white border border-slate-200/90 shadow-2xs'
                    : 'border border-transparent hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs sm:text-sm font-bold text-slate-900">Answer framework (STAR)</p>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/70 px-1.5 py-0.5 text-[10px] font-semibold">
                    Recommended
                  </span>
                  <span className="text-[11px] text-slate-400">5 min</span>
                </div>
              </button>

              {/* Tab 3 */}
              <button
                type="button"
                onClick={() => setActiveGuideTab('checklist')}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  activeGuideTab === 'checklist'
                    ? 'bg-white border border-slate-200/90 shadow-2xs'
                    : 'border border-transparent hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs sm:text-sm font-bold text-slate-900">Pre-interview checklist</p>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/70 px-1.5 py-0.5 text-[10px] font-semibold">
                    30 min before
                  </span>
                  <span className="text-[11px] text-slate-400">4 items</span>
                </div>
              </button>

              {/* Tab 4 */}
              <button
                type="button"
                onClick={() => setActiveGuideTab('mistakes')}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  activeGuideTab === 'mistakes'
                    ? 'bg-white border border-slate-200/90 shadow-2xs'
                    : 'border border-transparent hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs sm:text-sm font-bold text-slate-900">Common mistakes to avoid</p>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-md bg-amber-50 text-amber-700 border border-amber-200/70 px-1.5 py-0.5 text-[10px] font-semibold">
                    Watch out
                  </span>
                  <span className="text-[11px] text-slate-400">3 min</span>
                </div>
              </button>
            </div>

            {/* Right Content Panel */}
            <div className="md:col-span-8 p-6 lg:p-7 bg-white">
              {/* TAB 1 CONTENT: Camera & Setup */}
              {activeGuideTab === 'camera' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Look clear and sound clear</h3>
                    <p className="text-xs sm:text-sm text-slate-600 mt-1">
                      A clean setup shows you take the interview seriously, and it helps the AI hear you accurately.
                    </p>
                  </div>

                  <div className="space-y-4">
                    {/* Item 1 */}
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 border border-blue-100/80">
                        <Video className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Place the camera at eye level</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Stack books under a laptop if needed so you look straight ahead.
                        </p>
                      </div>
                    </div>

                    {/* Item 2 */}
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 border border-blue-100/80">
                        <Sun className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Face a window or soft light</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Light should fall on your face, not behind you.
                        </p>
                      </div>
                    </div>

                    {/* Item 3 */}
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 border border-blue-100/80">
                        <Home className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Keep the background simple</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          A plain wall or tidy shelf keeps attention on your answers.
                        </p>
                      </div>
                    </div>

                    {/* Item 4 */}
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 border border-blue-100/80">
                        <Headphones className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Test your audio with headphones</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Headphones reduce echo and make captions more accurate.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2 CONTENT: Answer Framework (STAR) */}
              {activeGuideTab === 'star' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Structure your answers with STAR</h3>
                    <p className="text-xs sm:text-sm text-slate-600 mt-1">
                      Deliver structured, evidence-backed answers to situational and architectural questions.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-100/80 font-bold text-xs">
                        S
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Situation — Set the scene</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Briefly describe the context, challenge, or system requirement you were addressing.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-100/80 font-bold text-xs">
                        T
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Task — State your responsibility</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Clarify what your specific role was and what goal you needed to accomplish.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-100/80 font-bold text-xs">
                        A
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Action — Detail the technical steps</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Explain what algorithms, technologies, or architectural patterns you chose and why.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-100/80 font-bold text-xs">
                        R
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Result — Share measured impact</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Highlight latency improvements, test coverage, uptime, or project milestones achieved.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3 CONTENT: Pre-interview checklist */}
              {activeGuideTab === 'checklist' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">30-minute pre-interview checklist</h3>
                    <p className="text-xs sm:text-sm text-slate-600 mt-1">
                      Quick checklist to eliminate distractions and prime your mindset for high performance.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100/80">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Review your key projects</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Be ready to discuss database schemas, APIs, and trade-offs on your listed CV projects.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100/80">
                        <Briefcase className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Review the target job description</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Check the core required skills and prepare 2–3 questions about the engineering stack.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100/80">
                        <Video className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Perform a 10-second setup test</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Verify your webcam lighting and microphone input levels in the portal preview.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100/80">
                        <Clock className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Silence notifications & hydrate</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Mute phone notifications, close extra tabs, and keep a glass of water nearby.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4 CONTENT: Common mistakes to avoid */}
              {activeGuideTab === 'mistakes' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Common mistakes to avoid</h3>
                    <p className="text-xs sm:text-sm text-slate-600 mt-1">
                      Top traps that lower candidate rubric depth and communication scores.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-700 border border-amber-100/80">
                        <Clock className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Talking too long without structure</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Aim for 90–120 seconds per answer. Focus on concrete engineering mechanics over rambling.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-700 border border-amber-100/80">
                        <AlertTriangle className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Saying "I don't know" without reasoning</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          If unsure, state your assumptions, break down first principles, and propose a solution.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-700 border border-amber-100/80">
                        <Shield className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Ignoring edge cases in coding</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Always check null inputs, empty arrays, large constraints, and algorithmic time complexity.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3.5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-700 border border-amber-100/80">
                        <HelpCircle className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-slate-900">Rushing without clarifying</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Take a 5-second pause to organize your thoughts before speaking your solution.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>

      {/* ========================================================================= */}
      {/* QUICK CAMERA & MICROPHONE TEST MODAL                                      */}
      {/* ========================================================================= */}
      {isTestingMedia && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">Camera & Microphone Preview</h3>
              <button
                type="button"
                onClick={() => stopMediaTest(false)}
                className="text-slate-400 hover:text-slate-600 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Confirm your video framing and speak a sentence to verify microphone input.
            </p>

            <div className="mt-4 relative aspect-video overflow-hidden rounded-xl bg-slate-950 border border-slate-200">
              <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover mirror" />

              {/* Audio meter pill overlay */}
              <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-full bg-slate-900/80 px-3 py-1 text-[11px] text-white backdrop-blur">
                <Mic className="h-3.5 w-3.5 text-indigo-400" />
                <span>Audio level</span>
                <div className="h-1.5 w-16 rounded-full bg-slate-700 overflow-hidden">
                  <div
                    className="h-full bg-emerald-400 transition-all duration-75"
                    style={{ width: `${audioLevel}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={() => stopMediaTest(false)}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => stopMediaTest(true)}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 shadow-sm"
              >
                Looks good, confirm test
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
