/**
 * Landing Page — HireSIGHT AI
 * Ultra-Modern, Premium Executive Homepage for Candidate & Recruiter AI Interview Intelligence
 */
import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  BrainCircuit,
  Sparkles,
  Code2,
  Video,
  Mic,
  Award,
  Layers,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Zap,
  TrendingUp,
  FileText,
  Users,
  Compass,
  Briefcase,
  Play,
  BarChart3,
  Lock,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState('recruiter');

  return (
    <>
      <Head>
        <title>HireSIGHT AI — Next-Gen Autonomous Interview Intelligence Platform</title>
        <meta
          name="description"
          content="Transform hiring with 5-dimensional explainable AI interviews, sandboxed coding execution, computer vision physical signals, and instant recruiter dossiers."
        />
      </Head>

      <div className="min-h-screen bg-[#F8FAFC] text-slate-900 selection:bg-indigo-500 selection:text-white">
        {/* ── STICKY NAVBAR ─────────────────────────────────────────────── */}
        <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-md transition-all">
          <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-black text-white shadow-md shadow-indigo-600/20">
                H
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-extrabold tracking-tight text-slate-900">
                  Hire<span className="text-indigo-600">SIGHT</span>
                </span>
                <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase -mt-1">
                  AI Interview Intelligence
                </span>
              </div>
            </div>

            {/* Nav Links (Desktop) */}
            <nav className="hidden items-center gap-8 md:flex text-sm font-semibold text-slate-600">
              <a href="#features" className="transition hover:text-indigo-600">Features</a>
              <a href="#scoring" className="transition hover:text-indigo-600">5D Scoring</a>
              <a href="#workflow" className="transition hover:text-indigo-600">How It Works</a>
              <a href="#roles" className="transition hover:text-indigo-600">Roles & Jobs</a>
            </nav>

            {/* Header Actions */}
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="hidden rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 sm:inline-block"
              >
                Candidate Sign In
              </Link>
              <Link
                href="/admin-login"
                className="rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs transition hover:bg-slate-50 hover:text-indigo-600"
              >
                Admin Portal
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-700 hover:shadow-indigo-600/30"
              >
                <span>Get Started</span>
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </header>

        {/* ── HERO SECTION ─────────────────────────────────────────────── */}
        <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
          {/* Subtle Ambient Background Gradients */}
          <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[600px] w-[1000px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-indigo-200/40 via-sky-100/40 to-transparent blur-3xl" />
          <div className="pointer-events-none absolute top-1/2 right-0 -z-10 h-[400px] w-[500px] rounded-full bg-violet-200/30 blur-3xl" />

          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-12 lg:grid-cols-12 lg:gap-8">
              {/* Left Column: Headlines & Action CTAs */}
              <div className="space-y-6 text-center lg:col-span-7 lg:text-left">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50/80 px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-indigo-700 shadow-xs backdrop-blur-sm">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Next-Gen Autonomous AI Interview Engine</span>
                </div>

                {/* Main Heading */}
                <h1 className="text-4xl font-black tracking-tight text-slate-900 sm:text-5xl lg:text-6xl leading-[1.12]">
                  Screen Candidate Talent with{' '}
                  <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-800 bg-clip-text text-transparent">
                    Mathematical Precision.
                  </span>
                </h1>

                {/* Subtitle */}
                <p className="mx-auto max-w-2xl text-base leading-relaxed text-slate-600 sm:text-lg lg:mx-0">
                  HireSIGHT replaces black-box evaluations with a comprehensive <strong>5-Dimensional scoring engine</strong>.
                  Quantify technical depth, sandboxed coding execution, vocal acoustics, and computer vision physical signals into 100% explainable recruiter dossiers.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-wrap items-center justify-center gap-4 pt-2 lg:justify-start">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3.5 text-base font-bold text-white shadow-lg shadow-indigo-600/25 transition hover:bg-indigo-700 hover:shadow-indigo-600/35"
                  >
                    <span>Start Candidate Assessment</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>

                  <Link
                    href="/jobs"
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3.5 text-base font-semibold text-slate-800 shadow-xs transition hover:bg-slate-50 hover:border-slate-300"
                  >
                    <Briefcase className="h-4 w-4 text-slate-500" />
                    <span>Explore Open Roles</span>
                  </Link>
                </div>

                {/* Trust Invariants */}
                <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs font-semibold text-slate-500 lg:justify-start">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span>100% Explainable Scoring</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span>Sandboxed Code Sandbox</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span>Zero Bias Rubrics</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Live Interactive Simulation Widget Card */}
              <div className="lg:col-span-5">
                <div className="relative mx-auto max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl transition hover:shadow-indigo-500/10">
                  {/* Card Header */}
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 text-sm font-bold text-white shadow-sm">
                        AC
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">Alex Chen</h4>
                        <p className="text-xs text-slate-500 font-medium">Senior Backend Engineer Candidate</p>
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Live Assessment
                    </span>
                  </div>

                  {/* Active Question Box */}
                  <div className="my-4 rounded-xl border border-slate-100 bg-slate-50/80 p-3.5">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        Active Technical Rubric (Q3 of 6)
                      </span>
                      <span className="text-[10px] font-semibold text-indigo-600">Adaptive Probe</span>
                    </div>
                    <p className="text-xs font-semibold leading-relaxed text-slate-800">
                      &quot;How do you architect distributed lock management in PostgreSQL to avoid write contention under high concurrency?&quot;
                    </p>
                  </div>

                  {/* 5-Dimensional Breakdown Preview */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-1.5 font-medium text-slate-700">
                        <Code2 className="h-3.5 w-3.5 text-indigo-600" />
                        Technical Depth (45%)
                      </span>
                      <span className="font-mono font-bold text-slate-900">92 / 100</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div className="h-full bg-indigo-600 rounded-full" style={{ width: '92%' }} />
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1">
                      <span className="flex items-center gap-1.5 font-medium text-slate-700">
                        <Layers className="h-3.5 w-3.5 text-emerald-600" />
                        Sandboxed Execution (25%)
                      </span>
                      <span className="font-mono font-bold text-emerald-700">100% Tests Pass</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: '100%' }} />
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1">
                      <span className="flex items-center gap-1.5 font-medium text-slate-700">
                        <Mic className="h-3.5 w-3.5 text-violet-600" />
                        Acoustics & Comm (15%)
                      </span>
                      <span className="font-mono font-bold text-slate-900">142 WPM • Clear</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div className="h-full bg-violet-500 rounded-full" style={{ width: '90%' }} />
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1">
                      <span className="flex items-center gap-1.5 font-medium text-slate-700">
                        <Video className="h-3.5 w-3.5 text-sky-600" />
                        Physical Gaze Stability (15%)
                      </span>
                      <span className="font-mono font-bold text-slate-900">95.4% Optimal</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div className="h-full bg-sky-500 rounded-full" style={{ width: '95%' }} />
                    </div>
                  </div>

                  {/* Decision Snapshot Footer */}
                  <div className="mt-5 flex items-center justify-between rounded-xl border border-indigo-100 bg-indigo-50/50 p-3.5">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                        Composite Recommendation
                      </span>
                      <span className="text-xs font-extrabold text-indigo-900">Strong Fit • 92.4 Composite</span>
                    </div>
                    <Link
                      href="/admin-dashboard"
                      className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs transition hover:bg-indigo-700"
                    >
                      Inspect Dossier
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── METRIC STATS BAR ─────────────────────────────────────────── */}
        <section className="border-y border-slate-200/80 bg-white py-8">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4 text-center">
              <div className="p-2">
                <p className="text-3xl font-black text-indigo-600 sm:text-4xl">100%</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Explainable Scoring Math</p>
              </div>
              <div className="p-2">
                <p className="text-3xl font-black text-slate-900 sm:text-4xl">&lt; 1.5s</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Sandboxed Test Execution</p>
              </div>
              <div className="p-2">
                <p className="text-3xl font-black text-emerald-600 sm:text-4xl">5-Pillars</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Holistic Multi-Modal Matrix</p>
              </div>
              <div className="p-2">
                <p className="text-3xl font-black text-violet-600 sm:text-4xl">0%</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Subjective Hallucination</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── 5-DIMENSIONAL SCORING ENGINE SPOTLIGHT ────────────────────── */}
        <section id="scoring" className="py-20 lg:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center space-y-3">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-indigo-700">
                <BrainCircuit className="h-3.5 w-3.5" />
                <span>The Core Innovation</span>
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
                The 5-Dimensional Explainable Scoring Engine
              </h2>
              <p className="text-base text-slate-600">
                Every score generated by HireSIGHT is mathematically computable from observable evaluations, isolated unit tests, and calibrated sensory tracking.
              </p>
            </div>

            <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {/* Pillar 1 */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs transition hover:shadow-md hover:border-indigo-300">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 mb-4">
                  <Code2 className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-bold text-slate-900">1. Technical Knowledge</h3>
                  <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">45% Weight</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-600">
                  Rubric evaluations assess conceptual depth (40%), technical accuracy (30%), and relevance (30%) across domain prompts.
                </p>
              </div>

              {/* Pillar 2 */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs transition hover:shadow-md hover:border-emerald-300">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 mb-4">
                  <Layers className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-bold text-slate-900">2. Coding Ability</h3>
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-bold text-emerald-700">25% Weight</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-600">
                  Sandboxed execution validates logic correctness, edge cases, and hidden unit test suites in Python and JavaScript.
                </p>
              </div>

              {/* Pillar 3 */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs transition hover:shadow-md hover:border-violet-300">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-50 text-violet-600 mb-4">
                  <Mic className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-bold text-slate-900">3. Communication</h3>
                  <span className="rounded-full bg-violet-50 px-2 py-0.5 text-xs font-bold text-violet-700">15% Weight</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-600">
                  Acoustic parameters quantify conversational speaking rate WPM, pause duration ratios, and terminology precision.
                </p>
              </div>

              {/* Pillar 4 */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs transition hover:shadow-md hover:border-amber-300">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 text-amber-600 mb-4">
                  <Video className="h-6 w-6" />
                </div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-bold text-slate-900">4. Behavioral Signals</h3>
                  <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-bold text-amber-700">15% Weight</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-600">
                  Computer vision tracks objective physical indicators: gaze stability ratio, head pose variance, and micro-movements.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS PIPELINE ─────────────────────────────────────── */}
        <section id="workflow" className="border-t border-slate-200/80 bg-white py-20 lg:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center space-y-3">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-indigo-700">
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Seamless Hiring Lifecycle</span>
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
                How HireSIGHT Works in 4 Simple Steps
              </h2>
              <p className="text-base text-slate-600">
                From job posting creation to candidate evaluation and one-click PDF decision dossiers.
              </p>
            </div>

            <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  step: '01',
                  title: 'Job & Role Setup',
                  desc: 'Admins create job listings or candidates select from open positions with skill prerequisites.',
                  icon: Briefcase,
                  color: 'indigo',
                },
                {
                  step: '02',
                  title: 'Autonomous AI Session',
                  desc: 'Adaptive voice and text interview questions probe technical depth with dynamic contextual follow-ups.',
                  icon: Play,
                  color: 'violet',
                },
                {
                  step: '03',
                  title: 'Sandboxed Code Test',
                  desc: 'Candidates write code in an interactive editor with automated unit tests and execution guardrails.',
                  icon: Code2,
                  color: 'emerald',
                },
                {
                  step: '04',
                  title: 'Explainable Dossier',
                  desc: 'Instant 5D score computation, tailored roadmap, and one-click executive PDF export.',
                  icon: FileText,
                  color: 'sky',
                },
              ].map((item) => (
                <div key={item.step} className="relative rounded-2xl border border-slate-200 bg-slate-50/50 p-6 shadow-xs">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl font-black text-slate-300">{item.step}</span>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white border border-slate-200 shadow-xs text-indigo-600">
                      <item.icon className="h-5 w-5" />
                    </div>
                  </div>
                  <h4 className="text-base font-bold text-slate-900 mb-2">{item.title}</h4>
                  <p className="text-xs leading-relaxed text-slate-600">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── AUDIENCE TAB EXPERIENCE (CANDIDATES VS RECRUITERS) ─────────── */}
        <section id="roles" className="py-20 lg:py-28 bg-[#F8FAFC]">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex justify-center mb-10">
              <div className="inline-flex rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xs">
                <button
                  type="button"
                  onClick={() => setActiveTab('recruiter')}
                  className={`rounded-xl px-6 py-2.5 text-sm font-bold transition ${
                    activeTab === 'recruiter'
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  For Recruiters & Admins
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('candidate')}
                  className={`rounded-xl px-6 py-2.5 text-sm font-bold transition ${
                    activeTab === 'candidate'
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  For Candidates & Engineers
                </button>
              </div>
            </div>

            {activeTab === 'recruiter' ? (
              <div className="rounded-3xl border border-slate-200 bg-white p-8 lg:p-12 shadow-sm">
                <div className="grid items-center gap-8 lg:grid-cols-2">
                  <div className="space-y-4">
                    <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold uppercase text-indigo-700">
                      Recruitment Control Center
                    </span>
                    <h3 className="text-2xl font-extrabold text-slate-900 sm:text-3xl">
                      Eliminate Hiring Bias. Accelerate Engineering Decisions.
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      HireSIGHT gives talent teams objective, structured evaluations. Inspect candidate rosters with multi-criteria filters, review 5-dimensional scores, and download publication-ready PDF reports.
                    </p>
                    <ul className="space-y-2.5 pt-2 text-xs font-semibold text-slate-700">
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Filter candidates by role, score bounds, recommendation, and activity dates.</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Full scoring formula audit modal reveals exact point contributions.</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Instant PDF and JSON export for applicant tracking integration.</span>
                      </li>
                    </ul>
                    <div className="pt-4">
                      <Link
                        href="/admin-login"
                        className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-xs font-bold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-700"
                      >
                        <span>Access Admin Dashboard</span>
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 shadow-inner">
                    <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-3">
                      <span className="text-xs font-bold text-slate-900">Admin Candidate Roster</span>
                      <span className="text-[10px] font-semibold text-indigo-600">Real-time Stream</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between rounded-xl bg-white p-3 border border-slate-200 shadow-xs">
                        <div>
                          <p className="font-bold text-slate-900">Sarah Jenkins</p>
                          <p className="text-[11px] text-slate-500">Full-Stack Lead • 6 yrs exp</p>
                        </div>
                        <div className="text-right">
                          <span className="rounded-lg bg-emerald-50 px-2 py-1 text-xs font-bold text-emerald-700 border border-emerald-200">
                            Strong Fit • 94.8
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between rounded-xl bg-white p-3 border border-slate-200 shadow-xs">
                        <div>
                          <p className="font-bold text-slate-900">Marcus Vance</p>
                          <p className="text-[11px] text-slate-500">ML Engineer • 4 yrs exp</p>
                        </div>
                        <div className="text-right">
                          <span className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-bold text-indigo-700 border border-indigo-200">
                            Potential Fit • 84.2
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-3xl border border-slate-200 bg-white p-8 lg:p-12 shadow-sm">
                <div className="grid items-center gap-8 lg:grid-cols-2">
                  <div className="space-y-4">
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold uppercase text-emerald-700">
                      Candidate Empowerment
                    </span>
                    <h3 className="text-2xl font-extrabold text-slate-900 sm:text-3xl">
                      Fair, Objective & Skill-Aligned Assessment.
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      Practice real-world engineering interviews under consistent conditions. Receive granular feedback on your technical depth, coding challenges, speech cadence, and tailored roadmaps for skill improvement.
                    </p>
                    <ul className="space-y-2.5 pt-2 text-xs font-semibold text-slate-700">
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Interactive live interview with smart contextual follow-up probing.</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Real in-browser coding runner supporting Python and JavaScript.</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Tailored remediation roadmap outlining exact competencies to master.</span>
                      </li>
                    </ul>
                    <div className="pt-4">
                      <Link
                        href="/register"
                        className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-xs font-bold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-700"
                      >
                        <span>Create Candidate Account</span>
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 shadow-inner">
                    <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-3">
                      <span className="text-xs font-bold text-slate-900">Tailored Remediation Roadmap</span>
                      <span className="text-[10px] font-semibold text-emerald-600">Actionable</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="rounded-xl bg-white p-3 border border-slate-200 shadow-xs">
                        <p className="font-bold text-slate-900 mb-0.5">1. Deepen Distributed Locking Concepts</p>
                        <p className="text-[11px] text-slate-500">Review Redlock algorithm and PostgreSQL advisory lock semantics under high contention.</p>
                      </div>
                      <div className="rounded-xl bg-white p-3 border border-slate-200 shadow-xs">
                        <p className="font-bold text-slate-900 mb-0.5">2. Master Asynchronous Event Loops</p>
                        <p className="text-[11px] text-slate-500">Practice microtask vs macrotask execution order in high-throughput node applications.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ── CALL TO ACTION BANNER ─────────────────────────────────────── */}
        <section className="py-16">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-8 text-white sm:p-12 lg:p-16 shadow-2xl">
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,0.25),_transparent_50%)]" />

              <div className="relative z-10 mx-auto max-w-3xl text-center space-y-6">
                <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl">
                  Ready to Transform Your Interview Experience?
                </h2>
                <p className="text-base text-slate-300 sm:text-lg">
                  Join candidates and hiring managers using HireSIGHT for fast, non-biased, and explainable technical evaluations.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-7 py-3.5 text-base font-bold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500"
                  >
                    <span>Create Free Account</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/login"
                    className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-7 py-3.5 text-base font-semibold text-white transition hover:bg-white/10"
                  >
                    <span>Candidate Sign In</span>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── FOOTER ───────────────────────────────────────────────────── */}
        <footer className="border-t border-slate-200 bg-white py-12 text-slate-600">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 font-black text-white text-sm">
                  H
                </div>
                <span className="text-base font-bold text-slate-900">
                  Hire<span className="text-indigo-600">SIGHT</span> AI
                </span>
                <span className="text-xs text-slate-400">© 2026 HireSIGHT Platform. All rights reserved.</span>
              </div>

              <div className="flex items-center gap-6 text-xs font-semibold">
                <Link href="/login" className="hover:text-indigo-600 transition">Candidate Login</Link>
                <Link href="/register" className="hover:text-indigo-600 transition">Register</Link>
                <Link href="/admin-login" className="hover:text-indigo-600 transition">Admin Portal</Link>
                <Link href="/jobs" className="hover:text-indigo-600 transition">Job Listings</Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
