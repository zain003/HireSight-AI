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
      if (result.match_percent >= 75) {
        setNotification('Accepted! You will be redirected to the interview test session.');
        setTimeout(() => router.push('/interview'), 3000);
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



        {/* ── Top Row: Profile + Job Selection + Upload ── */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Profile Card */}
          <div className="p-6 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-neon-violet to-neon-glow rounded-r" />
            <h3 className="text-lg font-bold text-deep-night mb-5 pl-4">Your Profile</h3>
            {profile ? (
              <div className="space-y-5 pl-4">
                {/* Domain & Role */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Domain</p>
                    <p className="text-deep-night font-medium text-sm">{profile.domain?.replace(/_/g, ' ')?.replace(/\b\w/g, c => c.toUpperCase()) || 'Not set'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Experience</p>
                    <p className="text-deep-night font-medium text-sm">{profile.experience_years ? `${profile.experience_years} years` : 'Not set'}</p>
                  </div>
                </div>
                {/* Job Titles */}
                {jobTitles.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Job Roles Detected</p>
                    <div className="flex flex-wrap gap-2">
                      {jobTitles.map((title, i) => (
                        <span key={i} className="px-3 py-1.5 bg-deep-night text-white rounded-lg text-xs font-medium">
                          {title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {/* Skills */}
                {skills.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Skills ({skills.length})</p>
                    <div className="flex flex-wrap gap-1.5">
                      {skills.map((skill, i) => (
                        <span key={i} className="px-2.5 py-1 bg-neon-violet/10 text-neon-violet rounded-lg text-xs font-medium hover:bg-neon-violet/15 transition-colors cursor-default">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {!skills.length && !jobTitles.length && (
                  <p className="text-text-muted text-sm">Upload your resume to populate your profile!</p>
                )}
              </div>
            ) : (
              <div className="pl-4">
                <div className="flex flex-col items-center py-6 text-center">
                  <div className="w-12 h-12 rounded-2xl bg-surface-subtle flex items-center justify-center mb-3">
                    <svg className="w-6 h-6 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <p className="text-text-muted text-sm">No profile yet. Upload your resume to get started!</p>
                </div>
              </div>
            )}
          </div>

          {/* Job Post Selection + Resume Upload + Match Result */}
          <div className="space-y-6">
            {/* Job Post Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-deep-night mb-2">Select a Job Post</label>
              <select
                className="w-full p-2 border border-deep-night/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-neon-violet"
                value={selectedJob?.id || ''}
                onChange={handleJobSelect}
              >
                <option value="" disabled>Select a job...</option>
                {jobPosts.map((job) => (
                  <option key={job.id} value={job.id}>{job.title}</option>
                ))}
              </select>
            </div>

            {/* Show job details if selected */}
            {selectedJob && (
              <div className="mb-4 p-4 bg-surface-subtle rounded-xl border border-deep-night/10">
                <h4 className="font-semibold text-deep-night mb-2">{selectedJob.title}</h4>
                <p className="text-text-muted mb-2">{selectedJob.description}</p>
                <div>
                  <span className="text-xs font-medium text-text-muted uppercase">Required Skills:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedJob.required_skills?.map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-neon-violet/10 text-neon-violet rounded-lg text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Resume Upload */}
            <ResumeUpload selectedJob={selectedJob} onUploadSuccess={handleUploadSuccess} onMatchResult={handleMatchResult} />
            {!selectedJob && (
              <p className="text-text-muted text-xs mt-2">Please select a job post to enable resume upload.</p>
            )}

            {/* Match Result Section */}
            {matchResult && (
              <div className="mt-4 p-4 bg-white border border-neon-violet/20 rounded-xl shadow-card">
                <h4 className="font-semibold text-neon-violet mb-2">Skill Match Result</h4>
                <div className="flex items-center gap-4 mb-2">
                  <span className="text-2xl font-bold text-deep-night">{matchResult.match_percent}%</span>
                  <div className="flex-1 h-4 bg-surface-subtle rounded-full overflow-hidden">
                    <div
                      className={`h-4 rounded-full ${matchResult.match_percent >= 75 ? 'bg-green-400' : matchResult.match_percent >= 50 ? 'bg-yellow-400' : 'bg-red-400'}`}
                      style={{ width: `${matchResult.match_percent}%` }}
                    />
                  </div>
                </div>
                <div className="text-sm text-text-muted mb-2">
                  {matchResult.match_percent >= 75 ? (
                    <span className="text-green-600 font-semibold">Accepted! Redirecting to interview session...</span>
                  ) : (
                    <span className="text-red-600 font-semibold">Rejected. You do not meet the criteria for this job.</span>
                  )}
                </div>
                {/* Show matched and missing skills */}
                <div className="mt-2">
                  <span className="text-xs font-medium text-text-muted uppercase">Matched Skills:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {matchResult.matched_skills?.map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-green-100 text-green-700 rounded-lg text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-2">
                  <span className="text-xs font-medium text-text-muted uppercase">Missing Skills:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {matchResult.missing_skills?.map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-red-100 text-red-700 rounded-lg text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Quick Actions ── */}
        <div className="mt-8 grid sm:grid-cols-3 gap-6">
          {[
            {
              icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                </svg>
              ),
              title: 'Start Interview', desc: 'Practice with AI-generated questions', action: null,
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              ),
              title: 'View History', desc: 'Check your past interviews', action: null,
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              ),
              title: 'Settings', desc: 'Customize your preferences', action: '/profile',
            },
          ].map((card, i) => (
            <div key={i} className="group p-6 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card hover:shadow-card-hover transition-all duration-300">
              <div className="w-11 h-11 rounded-xl bg-surface-subtle group-hover:bg-neon-violet/10 flex items-center justify-center mb-4 transition-colors duration-300">
                <div className="text-text-muted group-hover:text-neon-violet transition-colors duration-300">{card.icon}</div>
              </div>
              <h3 className="font-semibold text-deep-night mb-1">{card.title}</h3>
              <p className="text-text-muted text-sm mb-4 leading-relaxed">{card.desc}</p>
              {card.action ? (
                <a href={card.action} className="inline-flex items-center gap-1 text-sm font-medium text-neon-violet hover:text-neon-glow transition-colors">
                  Open
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                </a>
              ) : (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted/60 bg-surface-subtle px-3 py-1.5 rounded-lg">
                  <span className="w-1.5 h-1.5 rounded-full bg-dark-berry/40" />
                  Coming Soon
                </span>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
