/**
 * Dashboard Page
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import jobService from '@/services/jobService';
import CandidateHeader from '@/components/Candidate/CandidateHeader';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [jobPosts, setJobPosts] = useState([]);

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

  const handleLogout = () => authService.logout();

  /** Backend returns native arrays; tolerate legacy JSON strings. */
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

  const profileStatusFromApi = (p) => {
    if (!p) return 'No profile yet — complete setup after sign-in';
    const hasResume = !!(p.resume_path && String(p.resume_path).trim());
    const skills = normalizeStringList(p.skills);
    const experienced = normalizeStringList(p.experienced_skills);
    const known = normalizeStringList(p.known_skills);
    const skillSet = new Set([...skills, ...experienced, ...known]);
    const n = skillSet.size;
    const hasRole = !!(p.job_role && String(p.job_role).trim());
    const titles = normalizeStringList(p.job_titles);

    if (!hasResume) {
      if (n > 0) {
        return `${n} skill${n === 1 ? '' : 's'} on profile · upload a resume to link your CV`;
      }
      if (hasRole) {
        return `Target role set (${p.job_role.trim()}) · upload resume to continue`;
      }
      return 'Awaiting resume upload';
    }
    if (n > 0) {
      return `Resume on file · ${n} skill${n === 1 ? '' : 's'} extracted`;
    }
    if (titles.length > 0) {
      return 'Resume on file · titles extracted (skills pending)';
    }
    if (hasRole) {
      return 'Resume on file · role set (skills pending)';
    }
    return 'Resume on file · processing or empty extraction';
  };

  const topRoleFromApi = (p) => {
    if (!p) return 'Not set yet';
    const role = (p.job_role || '').trim();
    if (role) return role;
    const titles = normalizeStringList(p.job_titles);
    if (titles.length > 0) return titles[0];
    return 'Not detected yet — set role in profile or upload resume';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-300/30 border-t-indigo-300" />
          <p className="text-sm text-slate-300">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  const skills = normalizeStringList(profile?.skills);
  const topSkills = skills.slice(0, 8);
  const profileStatusText = profileStatusFromApi(profile);
  const topRoleText = topRoleFromApi(profile);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      <CandidateHeader activePath="/dashboard" user={user} onLogout={handleLogout} />

      <main className="container mx-auto space-y-8 px-6 py-8">
        <section className="overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 text-white shadow-xl backdrop-blur-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold">
                Welcome back, <span className="text-indigo-300">{user?.username}</span>
              </h2>
              <p className="mt-1 text-sm text-slate-300">
                Manage your profile, upload resume, and check interview readiness from one place.
              </p>
            </div>
            <button
              type="button"
              onClick={() => router.push('/interview-setup')}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:from-indigo-400 hover:to-violet-500 hover:shadow-indigo-500/40"
            >
              Configure & Start Interview
            </button>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-white/15 bg-slate-900/50 p-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-300">Profile status</p>
              <p className="mt-1 text-sm font-semibold leading-snug text-white">
                {profileStatusText}
              </p>
            </div>
            <div className="rounded-xl border border-white/15 bg-slate-900/50 p-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-300">Available jobs</p>
              <p className="mt-1 text-sm font-semibold text-white">{jobPosts.length}</p>
            </div>
            <div className="rounded-xl border border-white/15 bg-slate-900/50 p-4">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-300">Top role</p>
              <p className="mt-1 text-sm font-semibold text-white">{topRoleText}</p>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-white">Interview preparation guide</h3>
            <p className="mt-1 text-sm text-slate-300">
              Follow these steps to maximize your interview success rate.
            </p>
            <div className="mt-5 grid gap-4 lg:grid-cols-2">
              {[
                {
                  title: 'Camera & setup',
                  tag: 'Essential',
                  description: 'A clean, well-lit setup signals professionalism before you say a word.',
                  points: [
                    'Position camera at eye level',
                    'Face a window or use a ring light',
                    'Keep background clean and neutral',
                    'Test audio - use headphones to avoid echo',
                  ],
                  cta: 'Start setup check',
                  time: '5 min',
                  iconBg: 'bg-blue-500/20',
                  iconText: 'text-blue-300',
                },
                {
                  title: 'Answer framework (STAR)',
                  tag: 'Advanced',
                  description: 'Structure your answers to be clear, concise, and compelling.',
                  points: [
                    'Situation - Set the context briefly',
                    'Task - Describe your responsibility',
                    'Action - Explain exactly what you did',
                    'Result - Share measurable outcomes',
                  ],
                  cta: 'Practice with AI',
                  time: '15 min',
                  iconBg: 'bg-violet-500/20',
                  iconText: 'text-violet-300',
                },
                {
                  title: 'Pre-interview checklist',
                  tag: 'Tip',
                  description: 'Run this checklist 30 minutes before your interview starts.',
                  points: [
                    'Research company mission and recent news',
                    'Review the job description and your skills',
                    'Prepare 3 questions for the interviewer',
                    'Test join link, water on desk, phone silent',
                  ],
                  cta: 'Open checklist',
                  time: '10 min',
                  iconBg: 'bg-emerald-500/20',
                  iconText: 'text-emerald-300',
                },
                {
                  title: 'Common mistakes to avoid',
                  tag: 'Watch out',
                  description: 'Top reasons candidates get rejected - avoid these pitfalls.',
                  points: [
                    'Talking too long - keep answers under 2 min',
                    "Saying 'I don't know' without attempting to answer",
                    'Badmouthing previous employers',
                    'Not asking any question at the end',
                  ],
                  cta: 'See all tips',
                  time: '8 min',
                  iconBg: 'bg-amber-500/20',
                  iconText: 'text-amber-300',
                },
              ].map((card, idx) => (
                <div key={card.title} className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <div className={`flex h-6 w-6 items-center justify-center rounded-md ${card.iconBg}`}>
                      <span className={`text-xs font-bold ${card.iconText}`}>{idx + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{card.title}</p>
                      <span className="rounded-full border border-white/15 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                        {card.tag}
                      </span>
                    </div>
                  </div>

                  <p className="mb-3 text-xs text-slate-300">{card.description}</p>

                  <div className="space-y-1.5">
                    {card.points.map((point, pointIdx) => (
                      <div key={point} className="flex items-start gap-2">
                        <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-indigo-400/50 text-[10px] text-indigo-200">
                          {pointIdx + 1}
                        </span>
                        <p className="text-[11px] leading-relaxed text-slate-200">{point}</p>
                      </div>
                    ))}
                  </div>

                </div>
              ))}
            </div>
          </section>
      </main>
    </div>
  );
}
