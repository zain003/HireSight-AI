/**
 * Dashboard Page
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import ResumeUpload from '@/components/Resume/ResumeUpload';
import jobService from '@/services/jobService';
import resumeService from '@/services/resumeService';
import { useRef } from 'react';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [jobPosts, setJobPosts] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [notification, setNotification] = useState('');
  const fileInputRef = useRef();
  const [showAllSkills, setShowAllSkills] = useState(false);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadUserData();
    loadJobPosts();
  }, [router]);

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
      setJobPosts(posts);
    } catch (err) {
      // handle error
    }
  };

  const handleJobSelect = (e) => {
    const job = jobPosts.find(j => j.id === e.target.value);
    setSelectedJob(job);
    setMatchResult(null);
    setNotification('');
  };

  // Handle match result from ResumeUpload
  const handleMatchResult = (result) => {
    setMatchResult(result);
    if (result && typeof result.match_percent === 'number') {
      if (result.match_percent >= 70) {
        setNotification('You are eligible for the interview test based on your skill match.');
      } else {
        setNotification('You do not meet the criteria for this job. Better luck next time!');
      }
    }
  };

  const handleLogout = () => authService.logout();

  // Safe JSON parse helper
  const parseJSON = (str) => {
    if (!str) return [];
    // Backend now stores/returns arrays natively (MongoDB + Pydantic)
    if (Array.isArray(str)) return str;
    if (typeof str === 'object') return str;
    try { return JSON.parse(str); } catch { return []; }
  };

  // Handle resume upload success: reload profile
  const handleUploadSuccess = async () => {
    try {
      const profileData = await authService.getProfile();
      setProfile(profileData);
      setNotification('Resume parsed and profile updated!');
    } catch (err) {
      setNotification('Resume parsed, but failed to reload profile.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-neon-violet/30 border-t-neon-violet animate-spin" />
          <p className="text-text-muted text-sm">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  const skills = parseJSON(profile?.skills);
  const jobTitles = parseJSON(profile?.job_titles);
  const education = parseJSON(profile?.education);
  const projects = parseJSON(profile?.projects);
  const certifications = parseJSON(profile?.certifications);
  const companies = parseJSON(profile?.companies);

  const topSkills = skills.slice(0, 12);
  const hasMoreSkills = skills.length > topSkills.length;
  const displaySkills = showAllSkills ? skills : topSkills;

  return (
    <div className="min-h-screen bg-white">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-deep-night/[0.06]">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <a href="/" className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-deep-night tracking-tight">
              Hire<span className="text-neon-glow">SIGHT</span>
            </h1>
          </a>
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neon-violet to-neon-glow flex items-center justify-center">
                <span className="text-white text-xs font-bold">
                  {user?.username?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              </div>
              <span className="text-deep-night text-sm font-medium hidden sm:inline">{user?.username}</span>
            </div>
            <button onClick={handleLogout} className="px-4 py-2 text-sm font-medium text-text-muted border border-deep-night/[0.08] rounded-xl hover:text-deep-night hover:border-deep-night/20 hover:bg-surface-subtle">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="container mx-auto px-6 py-10 animate-fade-in">
        {/* Welcome */}
        <div className="mb-10">
          <h2 className="text-2xl font-bold text-deep-night">
            Welcome back, <span className="text-neon-glow">{user?.username}</span>
          </h2>
          <p className="text-text-muted mt-1">Here&apos;s your interview preparation overview</p>
        </div>



        {/* ── Main grid: Profile + Workflow ── */}
        <div className="grid lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1.6fr)] gap-8">
          {/* Profile summary */}
          <div className="border border-deep-night/[0.08] bg-white p-6 flex flex-col gap-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-surface-subtle border border-deep-night/20 flex items-center justify-center">
                  <span className="text-sm font-semibold">
                    {user?.username?.charAt(0)?.toUpperCase() || 'U'}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-deep-night">
                    {user?.username}
                  </p>
                  <p className="text-[11px] text-text-muted">
                    {jobTitles[0] || 'No role detected yet'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[11px] tracking-[0.16em] uppercase text-text-muted">
                  Profile status
                </p>
                <p className="mt-1 inline-block px-2 py-1 text-[11px] border border-deep-night/20 bg-surface-subtle">
                  {skills.length ? 'Resume parsed' : 'Awaiting resume'}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.16em] mb-1">
                  Domain
                </p>
                <p className="text-deep-night">
                  {profile?.domain
                    ?.replace(/_/g, ' ')
                    ?.replace(/\b\w/g, c => c.toUpperCase()) || 'Not set'}
                </p>
              </div>
              <div>
                <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.16em] mb-1">
                  Experience
                </p>
                <p className="text-deep-night">
                  {profile?.experience_years ? `${profile.experience_years} years` : 'Not set'}
                </p>
              </div>
            </div>

            {topSkills.length > 0 ? (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.16em]">
                    Top skills
                  </p>
                  <div className="flex items-center gap-3">
                    <p className="text-[11px] text-text-muted">
                      {skills.length} skills extracted
                    </p>
                    {hasMoreSkills && (
                      <button
                        type="button"
                        onClick={() => setShowAllSkills(!showAllSkills)}
                        className="text-[11px] text-neon-violet underline underline-offset-2"
                      >
                        {showAllSkills ? 'Show less' : 'Show all'}
                      </button>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {displaySkills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 text-[11px] border border-deep-night/15 bg-surface-subtle"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-text-muted text-xs mt-2">
                Upload your resume to build your structured skill profile.
              </p>
            )}
          </div>

          {/* Right column: workflow */}
          <div className="flex flex-col gap-6">
            {/* Step 1: job selection */}
            <div className="border border-deep-night/[0.08] bg-white p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[11px] tracking-[0.18em] uppercase text-text-muted">
                  Step 01 · Select job
                </p>
              </div>
              <label className="block text-xs font-medium text-deep-night mb-1">
                Job post
              </label>
              <select
                className="w-full px-3 py-2 border border-deep-night/15 text-sm focus:outline-none focus:ring-1 focus:ring-neon-violet bg-white"
                value={selectedJob?.id || ''}
                onChange={handleJobSelect}
              >
                <option value="" disabled>Select a job…</option>
                {jobPosts.map((job) => (
                  <option key={job.id} value={job.id}>{job.title}</option>
                ))}
              </select>
            </div>

            {/* Step 2: job details + upload */}
            {selectedJob && (
              <div className="border border-deep-night/[0.08] bg-surface-subtle p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] tracking-[0.18em] uppercase text-text-muted mb-1">
                      Step 02 · Review role
                    </p>
                    <h3 className="text-sm font-semibold text-deep-night">
                      {selectedJob.title}
                    </h3>
                  </div>
                </div>
                <p className="text-xs text-text-muted line-clamp-3">
                  {selectedJob.description}
                </p>
                <div>
                  <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.16em] mb-2">
                    Required skills
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedJob.required_skills?.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 text-[11px] border border-deep-night/15 bg-white"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: upload & match */}
            <div className="border border-deep-night/[0.08] bg-white p-5">
              <p className="text-[11px] tracking-[0.18em] uppercase text-text-muted mb-3">
                Step 03 · Upload resume & match
              </p>
              <ResumeUpload
                selectedJob={selectedJob}
                onUploadSuccess={handleUploadSuccess}
                onMatchResult={handleMatchResult}
              />
            </div>
            {!selectedJob && (
              <p className="text-text-muted text-xs mt-2">Please select a job post to enable resume upload.</p>
            )}

            {/* Match Result Section */}
            {matchResult && (
              <div className="border border-deep-night/[0.08] bg-white p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] tracking-[0.18em] uppercase text-text-muted mb-1">
                      Match summary
                    </p>
                    <p className="text-xs text-text-muted">
                      Comparison between your extracted skills and role requirements.
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-deep-night text-right">
                      {matchResult.match_percent}%
                    </p>
                    <p className="text-[11px] text-text-muted">
                      Skill match
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex-1 h-3 bg-surface-subtle border border-deep-night/10">
                    <div
                      className={`h-full ${matchResult.match_percent >= 70 ? 'bg-green-500' : matchResult.match_percent >= 50 ? 'bg-yellow-400' : 'bg-red-400'}`}
                      style={{ width: `${matchResult.match_percent}%` }}
                    />
                  </div>
                  <span
                    className={`px-2 py-1 text-[11px] border ${
                      matchResult.match_percent >= 70
                        ? 'border-green-500 text-green-700 bg-green-50'
                        : 'border-red-500 text-red-700 bg-red-50'
                    }`}
                  >
                    {matchResult.match_percent >= 70 ? 'Eligible for interview' : 'Below threshold'}
                  </span>
                </div>

                <div className="grid md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.16em] mb-2">
                      Matched skills
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {(matchResult.matched_skills || []).slice(0, 10).map((skill, i) => (
                        <span key={i} className="px-2 py-1 border border-green-400/60 bg-green-50 text-green-700">
                          {skill}
                        </span>
                      ))}
                      {matchResult.matched_skills && matchResult.matched_skills.length > 10 && (
                        <span className="px-2 py-1 border border-green-400/60 bg-green-50 text-green-700">
                          +{matchResult.matched_skills.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.16em] mb-2">
                      Missing required skills
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {(matchResult.missing_skills || []).slice(0, 8).map((skill, i) => (
                        <span key={i} className="px-2 py-1 border border-red-400/60 bg-red-50 text-red-700">
                          {skill}
                        </span>
                      ))}
                      {matchResult.missing_skills && matchResult.missing_skills.length > 8 && (
                        <span className="px-2 py-1 border border-red-400/60 bg-red-50 text-red-700">
                          +{matchResult.missing_skills.length - 8} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Bottom toolbar ── */}
        <div className="mt-10 border-t border-deep-night/[0.06] pt-4 flex flex-wrap items-center justify-between gap-3 text-[11px] text-text-muted">
          <div className="flex items-center gap-3">
            <span className="px-2 py-1 border border-deep-night/15 bg-surface-subtle">
              Coming soon: AI interview practice
            </span>
            <span>Start mock sessions and review past interviews.</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="/profile" className="underline underline-offset-2">
              Profile settings
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
