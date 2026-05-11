/**
 * Landing Page — HireSIGHT AI
 */

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-900 text-white">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,0.35),_transparent_45%)]" />
        <div className="relative container mx-auto px-6 py-10 md:py-14">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-extrabold tracking-tight">
              Hire<span className="text-indigo-300">SIGHT</span> AI
            </h1>
            <a href="/admin-login" className="border border-white/30 px-5 py-2.5 text-base font-medium hover:bg-white/10">
              Admin Console
            </a>
          </div>

          <div className="grid items-center gap-7 lg:grid-cols-2">
            <div className="space-y-5">
              <div className="inline-block border border-indigo-300/40 bg-indigo-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-indigo-200">
                AI Interview Intelligence Platform
              </div>
              <h2 className="text-4xl font-bold leading-tight md:text-5xl">
                Hire better candidates with structured AI interviews.
              </h2>
              <p className="max-w-xl text-base text-slate-300 md:text-lg">
                Convert job descriptions and resumes into skill-aligned interviews, then evaluate candidates with consistent standards.
              </p>
              <div className="flex flex-wrap gap-3">
                <a href="/register" className="neon-btn px-7 py-3 text-sm font-semibold">
                  Create Candidate Account
                </a>
                <a href="/login" className="border border-white/30 bg-white/5 px-7 py-3 text-sm font-semibold hover:bg-white/15">
                  Candidate Sign In
                </a>
              </div>
            </div>

            <div className="rounded-2xl border border-white/20 bg-slate-900/55 p-6 shadow-2xl backdrop-blur-sm">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Interview Session Snapshot</h3>
                <span className="rounded-full border border-indigo-300/40 bg-indigo-400/10 px-3 py-1 text-xs font-medium text-indigo-200">
                  Live Analysis
                </span>
              </div>
              <div className="mb-4 rounded-xl border border-white/15 bg-slate-950/40 p-4">
                <p className="mb-3 text-xs uppercase tracking-[0.18em] text-slate-400">Current Question</p>
                <p className="text-sm leading-relaxed text-slate-100">
                  Explain how you would evaluate and improve model performance after deployment in production.
                </p>
              </div>
              <div className="grid gap-3 text-sm">
                <div className="flex items-center justify-between rounded-lg border border-white/15 bg-slate-950/35 px-4 py-3">
                  <span className="text-slate-300">Resume Skill Parsing</span>
                  <span className="font-semibold text-emerald-300">Complete</span>
                </div>
                <div className="flex items-center justify-between rounded-lg border border-white/15 bg-slate-950/35 px-4 py-3">
                  <span className="text-slate-300">Role Match Score</span>
                  <span className="font-semibold text-indigo-200">82%</span>
                </div>
                <div className="flex items-center justify-between rounded-lg border border-white/15 bg-slate-950/35 px-4 py-3">
                  <span className="text-slate-300">Interview Readiness</span>
                  <span className="font-semibold text-amber-300">In Progress</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="container mx-auto px-6 py-16">
        <div className="mb-10 text-center">
          <h3 className="text-3xl font-bold text-slate-900">Built for modern interview workflows</h3>
          <p className="mx-auto mt-3 max-w-2xl text-slate-500">
            A complete pipeline for recruiters, hiring managers, and candidates.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {[
            ['Role Intelligence', 'Extract required skills from job descriptions and build role-specific interview criteria.'],
            ['Candidate Profiling', 'Parse resumes into structured capabilities and compare against role benchmarks.'],
            ['Interview Automation', 'Generate targeted questions with consistent scoring for fair evaluations.'],
          ].map(([title, desc]) => (
            <div key={title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h4 className="mb-2 text-lg font-semibold text-slate-900">{title}</h4>
              <p className="text-sm leading-relaxed text-slate-600">{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
