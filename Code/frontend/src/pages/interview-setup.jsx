import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import {
  FileText,
  UserCheck,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  ArrowLeft,
  Briefcase,
  CheckCircle,
} from 'lucide-react';
import authService from '@/services/authService';
import interviewService from '@/services/interviewService';
import jobService from '@/services/jobService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';
import InterviewConfigCard from '@/components/Interview/InterviewConfigCard';
import { formatApiDetail } from '@/utils/formatApiDetail';

export default function InterviewSetupPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [jobPost, setJobPost] = useState(null);
  const [codingLanguage, setCodingLanguage] = useState('javascript');
  const [roleFit, setRoleFit] = useState(null);
  const [loadingFit, setLoadingFit] = useState(false);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [networkError, setNetworkError] = useState(false);

  // Normalize string lists from profile/backend
  const normalizeList = useCallback((val) => {
    if (val == null) return [];
    if (Array.isArray(val)) return val.map((s) => String(s).trim()).filter(Boolean);
    if (typeof val === 'string') {
      try {
        const p = JSON.parse(val);
        return Array.isArray(p) ? p.map((s) => String(s).trim()).filter(Boolean) : [];
      } catch {
        return [val.trim()].filter(Boolean);
      }
    }
    return [];
  }, []);

  const profileSkills = useMemo(() => {
    if (!profile) return [];
    const base = normalizeList(profile.skills);
    const exp = normalizeList(profile.experienced_skills);
    const known = normalizeList(profile.known_skills);
    return Array.from(new Set([...base, ...exp, ...known]));
  }, [profile, normalizeList]);

  // Load user, job post (if any), and profile
  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError('');
    setNetworkError(false);

    try {
      if (!authService.isAuthenticated()) {
        router.push('/login');
        return;
      }

      const userData = await authService.getCurrentUser();
      setUser(userData);

      let userProfile = null;
      try {
        userProfile = await authService.getProfile();
        setProfile(userProfile);
      } catch (err) {
        console.log('No profile found, proceeding with defaults');
      }

      const queryJobPostId = router.query.jobPostId;
      if (queryJobPostId && typeof queryJobPostId === 'string') {
        try {
          const loadedJobPost = await jobService.getJobPost(queryJobPostId);
          setJobPost(loadedJobPost);
        } catch (err) {
          console.warn('Could not load specific job post:', err);
        }
      }
    } catch (err) {
      console.error('Failed to load interview setup:', err);
      setNetworkError(true);
      setError('Unable to load interview configuration.');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (router.isReady) {
      loadInitialData();
    }
  }, [router.isReady, loadInitialData]);

  const handleStartInterview = async ({ jobRole: chosenRole, codingLanguage: chosenLang }) => {
    setSubmitting(true);
    setError('');

    try {
      const numQuestions = router.query.num_questions
        ? Math.max(4, Math.min(30, parseInt(router.query.num_questions, 10) || 20))
        : 20;

      const effectiveRoleName = jobPost?.title || chosenRole || profile?.job_role || 'Software Engineer';
      let effectiveSkills = [...profileSkills];

      if (jobPost?.required_skills && Array.isArray(jobPost.required_skills)) {
        effectiveSkills = Array.from(new Set([...effectiveSkills, ...jobPost.required_skills]));
      }

      const payload = {
        job_role: effectiveRoleName,
        candidate_skills: effectiveSkills,
        num_questions: numQuestions,
        ...(jobPost?.id || router.query.jobPostId
          ? { job_post_id: jobPost?.id || router.query.jobPostId }
          : {}),
        ...(jobPost?.description ? { job_description: jobPost.description } : {}),
      };

      // Launch live interview session
      const data = await interviewService.startSession(payload);
      if (data?.session_id) {
        if (typeof window !== 'undefined' && Array.isArray(data.questions) && data.questions.length > 0) {
          sessionStorage.setItem(
            'hiresight_questions_' + data.session_id,
            JSON.stringify(data.questions)
          );
        }
        // Route to interview room with session parameters
        router.push({
          pathname: '/interview',
          query: {
            sessionId: data.session_id,
            role: effectiveRoleName,
            lang: chosenLang,
          },
        });
      } else {
        router.push('/interview');
      }
    } catch (err) {
      console.error('Failed to start interview session:', err);
      setError(
        formatApiDetail(err.response?.data?.detail) ||
        'Failed to initialize live interview session. Please try again.'
      );
      setSubmitting(false);
    }
  };

  const handleLogout = () => authService.logout();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f8fafc]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-2 border-indigo-600/20 border-t-indigo-600" />
          <p className="text-xs font-medium text-slate-500">Loading interview configuration engine…</p>
        </div>
      </div>
    );
  }

  const activeJobTitle = jobPost?.title || profile?.job_role || 'Software Engineer';

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-800 antialiased font-sans">
      <Head>
        <title>Interview Setup — HireSight AI</title>
        <meta name="description" content="Review job requirements, matched CV profile, and 4-phase interview agenda." />
      </Head>

      <CandidateHeader activePath="/interview-setup" user={user} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => router.push('/dashboard')}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 shadow-2xs"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Dashboard
          </button>

          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-100 px-3 py-1 rounded-full">
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI Role-Adaptive Assessment Engine</span>
          </div>
        </div>

        {/* Network Error Banner with Retry */}
        {networkError && (
          <div className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 shadow-xs">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0" />
              <div>
                <p className="font-bold text-slate-900">Configuration Service Warning</p>
                <p className="text-xs text-slate-600 mt-0.5">{error}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={loadInitialData}
              className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 shadow-2xs"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry Connection
            </button>
          </div>
        )}

        {/* Candidate Profile Context Banner */}
        <section className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-3 py-0.5 text-xs font-semibold text-blue-700">
                <UserCheck className="h-3.5 w-3.5" />
                Live Interview Readiness
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                {activeJobTitle} Assessment
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
                Questions are generated in real-time by the AI interviewer based on the job posting requirements and your verified CV profile.
              </p>
            </div>

            {jobPost && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-3.5 text-right shadow-2xs">
                <div className="flex items-center justify-end gap-1 text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                  <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
                  Eligible for Interview
                </div>
                <p className="text-xs sm:text-sm font-bold text-slate-900">{jobPost.title}</p>
                <p className="text-[11px] text-slate-500">{jobPost.domain || 'Engineering'}</p>
              </div>
            )}
          </div>

          {/* Profile Skill Snapshot */}
          <div className="mt-6 pt-6 border-t border-slate-100 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                <FileText className="h-3.5 w-3.5 text-blue-700" />
                Resume Status
              </div>
              <p className="mt-1.5 text-sm font-bold text-slate-900">
                {profile?.resume_path ? 'CV on File' : 'Profile Active'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {profile?.resume_path ? 'Skills & experience linked' : 'Calibrated to target role'}
              </p>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                <Briefcase className="h-3.5 w-3.5 text-emerald-600" />
                Detected Skills
              </div>
              <p className="mt-1.5 text-sm font-bold text-slate-900">
                {profileSkills.length} Technical Skills
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {profileSkills.slice(0, 4).map((sk) => (
                  <span key={sk} className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-medium text-slate-700 shadow-2xs">
                    {sk}
                  </span>
                ))}
                {profileSkills.length > 4 && (
                  <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-medium text-slate-500 shadow-2xs">
                    +{profileSkills.length - 4} more
                  </span>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                <CheckCircle className="h-3.5 w-3.5 text-blue-700" />
                Target Role
              </div>
              <p className="mt-1.5 text-sm font-bold text-slate-900">
                {activeJobTitle}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {jobPost?.domain || 'Engineering Department'}
              </p>
            </div>
          </div>
        </section>

        {/* Focused Configuration & 4-Phase Agenda Card */}
        <InterviewConfigCard
          jobPost={jobPost}
          jobRole={activeJobTitle}
          requiredSkills={jobPost?.required_skills || []}
          candidateSkills={profileSkills}
          candidateProjects={profile?.projects || []}
          codingLanguage={codingLanguage}
          onSelectCodingLanguage={setCodingLanguage}
          roleFit={roleFit}
          loadingFit={loadingFit}
          onStartInterview={handleStartInterview}
          loading={submitting}
          error={error}
        />
      </main>
    </div>
  );
}
