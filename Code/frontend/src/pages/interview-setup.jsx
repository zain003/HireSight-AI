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

const DEFAULT_ROLES = [
  {
    role_id: 'frontend_engineer',
    display_name: 'Frontend Engineer',
    inferred_seniority: 'mid',
    competency_areas: ['Core Web Technologies', 'Modern UI Frameworks (React)', 'State Management', 'Web Performance'],
  },
  {
    role_id: 'backend_engineer',
    display_name: 'Backend Engineer',
    inferred_seniority: 'mid',
    competency_areas: ['API & Microservices Design', 'Database Architecture & SQL', 'Concurrency & Distributed Systems'],
  },
  {
    role_id: 'fullstack_engineer',
    display_name: 'Full-Stack Engineer',
    inferred_seniority: 'mid',
    competency_areas: ['Frontend & Backend Architecture', 'REST & GraphQL APIs', 'Database Integration', 'End-to-End Testing'],
  },
  {
    role_id: 'devops_engineer',
    display_name: 'DevOps & Cloud Infrastructure',
    inferred_seniority: 'mid',
    competency_areas: ['CI/CD Pipelines & Automation', 'Containers & Kubernetes', 'Cloud Architecture (AWS/GCP/Azure)'],
  },
  {
    role_id: 'data_engineer',
    display_name: 'Data & Analytics Engineer',
    inferred_seniority: 'mid',
    competency_areas: ['Data Pipeline & ETL Engineering', 'Distributed Big Data (Spark/Flink)', 'Data Warehousing & SQL'],
  },
  {
    role_id: 'ml_engineer',
    display_name: 'Machine Learning / AI Engineer',
    inferred_seniority: 'mid',
    competency_areas: ['ML Algorithms & Math', 'Deep Learning & Neural Networks', 'MLOps & Model Deployment', 'LLMs & GenAI'],
  },
  {
    role_id: 'qa_automation_engineer',
    display_name: 'QA Automation Engineer',
    inferred_seniority: 'mid',
    competency_areas: ['Test Automation Frameworks', 'API & Integration Testing', 'Performance & Load Testing'],
  },
];

export default function InterviewSetupPage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [jobPost, setJobPost] = useState(null);
  const [roles, setRoles] = useState(DEFAULT_ROLES);
  const [selectedRoleId, setSelectedRoleId] = useState('backend_engineer');
  const [seniority, setSeniority] = useState('mid');
  const [codingLanguage, setCodingLanguage] = useState('python');
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

  // Load user and initial role configs
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

      // If jobPostId is present in query, fetch job details
      const queryJobPostId = router.query.jobPostId;
      if (queryJobPostId && typeof queryJobPostId === 'string') {
        try {
          const jobData = await jobService.getJobPost(queryJobPostId);
          setJobPost(jobData);
        } catch (err) {
          console.warn('Could not load specific job post:', err);
        }
      }

      const expYears = userProfile?.years_of_experience || userProfile?.experience_years || null;
      const roleConfigRes = await interviewService.getRoleConfigs(expYears);
      const fetchedRoles = roleConfigRes?.roles || [];
      setRoles(fetchedRoles);

      if (fetchedRoles.length > 0) {
        // Map target role from profile or job post if matching
        const candidateTarget = (userProfile?.job_role || '').toLowerCase().replace(/\s+/g, '_');
        const matchedRole = fetchedRoles.find(
          (r) =>
            r.role_id === candidateTarget ||
            candidateTarget.includes(r.role_id) ||
            r.display_name.toLowerCase().includes((userProfile?.job_role || '').toLowerCase())
        );

        const initialRole = matchedRole || fetchedRoles[0];
        setSelectedRoleId(initialRole.role_id);
        setSeniority(initialRole.inferred_seniority || 'mid');
      }
    } catch (err) {
      console.error('Failed to load interview setup:', err);
      setNetworkError(true);
      setError('Unable to load role configurations from server. Please check connection and retry.');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (router.isReady) {
      loadInitialData();
    }
  }, [router.isReady, loadInitialData]);

  // Recalculate role fit on role change
  useEffect(() => {
    if (!selectedRoleId) return;

    let isMounted = true;
    const computeFit = async () => {
      setLoadingFit(true);
      try {
        const fitData = await interviewService.getRoleFit(
          selectedRoleId,
          profileSkills,
          profile?.experience_years || null
        );
        if (isMounted) {
          setRoleFit(fitData);
        }
      } catch (err) {
        if (isMounted) {
          setRoleFit(null);
        }
      } finally {
        if (isMounted) setLoadingFit(false);
      }
    };

    computeFit();

    return () => {
      isMounted = false;
    };
  }, [selectedRoleId, profileSkills, profile]);

  const handleStartInterview = async ({ roleId, roleDisplayName, seniority: chosenSeniority, codingLanguage: chosenLang }) => {
    setSubmitting(true);
    setError('');

    try {
      const payload = {
        job_role: roleDisplayName,
        candidate_skills: profileSkills,
        num_questions: 20,
        ...(jobPost?.id || router.query.jobPostId ? { job_post_id: jobPost?.id || router.query.jobPostId } : {}),
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
            role: roleId,
            seniority: chosenSeniority,
            lang: chosenLang,
          },
        });
      } else {
        router.push('/interview');
      }
    } catch (err) {
      console.error('Failed to start interview session:', err);
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to initialize live interview session. Please try again.');
      setSubmitting(false);
    }
  };

  const handleLogout = () => authService.logout();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
          <p className="text-sm font-medium text-slate-300">Loading interview configuration engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100">
      <Head>
        <title>Pre-Interview Setup — HireSIGHT AI</title>
        <meta name="description" content="Configure target role, seniority tier, and review interview agenda." />
      </Head>

      <CandidateHeader activePath="/interview-setup" user={user} onLogout={handleLogout} />

      <main className="container mx-auto max-w-6xl space-y-8 px-6 py-8">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => router.push('/dashboard')}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-slate-900/60 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/10 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </button>

          <div className="flex items-center gap-2 text-xs font-medium text-indigo-300">
            <Sparkles className="h-4 w-4" />
            <span>AI Multimodal Evaluation Engine</span>
          </div>
        </div>

        {/* Network Error Banner with Retry */}
        {networkError && (
          <div className="flex items-center justify-between rounded-2xl border border-red-500/30 bg-red-950/50 p-5 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-red-400" />
              <div>
                <p className="font-semibold text-red-100">Configuration Service Offline</p>
                <p className="text-xs text-red-300">{error}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={loadInitialData}
              className="inline-flex items-center gap-2 rounded-xl bg-red-500/20 px-4 py-2 text-xs font-semibold text-red-200 border border-red-500/40 hover:bg-red-500/30"
            >
              <RefreshCw className="h-4 w-4" />
              Retry Connection
            </button>
          </div>
        )}

        {/* Candidate Profile Context Banner */}
        <section className="overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 shadow-xl backdrop-blur-md">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3 py-0.5 text-xs font-medium text-indigo-300">
                <UserCheck className="h-3.5 w-3.5" />
                Step 1 of 2: Pre-Interview Assessment Calibration
              </div>
              <h1 className="text-2xl font-black text-white sm:text-3xl">
                Interview Readiness & Role Calibration
              </h1>
              <p className="text-sm text-slate-300">
                Review your extracted profile attributes, customize your assessment targets, and inspect the grading agenda.
              </p>
            </div>

            {jobPost && (
              <div className="rounded-xl border border-indigo-400/30 bg-indigo-950/40 p-3 text-right">
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-300">Applying For</span>
                <p className="text-sm font-bold text-white">{jobPost.title}</p>
                <p className="text-xs text-slate-400">{jobPost.department || 'Engineering'}</p>
              </div>
            )}
          </div>

          {/* Profile Skill Snapshot */}
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <FileText className="h-4 w-4 text-indigo-400" />
                Resume Status
              </div>
              <p className="mt-2 text-sm font-semibold text-white">
                {profile?.resume_path ? 'CV On File & Analyzed' : 'No Resume Uploaded'}
              </p>
              <p className="text-xs text-slate-400">
                {profile?.resume_path ? 'Skills extracted automatically' : 'Role matched via manual selection'}
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <Briefcase className="h-4 w-4 text-emerald-400" />
                Detected Skills
              </div>
              <p className="mt-2 text-sm font-semibold text-white">
                {profileSkills.length} Technical Skills
              </p>
              <div className="mt-1 flex flex-wrap gap-1">
                {profileSkills.slice(0, 4).map((sk) => (
                  <span key={sk} className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-slate-300">
                    {sk}
                  </span>
                ))}
                {profileSkills.length > 4 && (
                  <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-slate-400">
                    +{profileSkills.length - 4} more
                  </span>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <CheckCircle className="h-4 w-4 text-sky-400" />
                Target Alignment
              </div>
              <p className="mt-2 text-sm font-semibold text-white">
                {profile?.job_role || 'General Software Engineering'}
              </p>
              <p className="text-xs text-slate-400">
                Inferred: {profile?.experience_years ? `${profile.experience_years} years exp` : 'Standard Calibration'}
              </p>
            </div>
          </div>

          {profileSkills.length === 0 && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-950/30 p-3 text-xs text-amber-200">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
              <span>
                No resume skills detected. You can select any role and difficulty tier below to generate standard benchmark questions.
              </span>
            </div>
          )}
        </section>

        {/* Core Configuration & Agenda Card Component */}
        <InterviewConfigCard
          roles={roles}
          selectedRoleId={selectedRoleId}
          onSelectRole={setSelectedRoleId}
          seniority={seniority}
          onSelectSeniority={setSeniority}
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
