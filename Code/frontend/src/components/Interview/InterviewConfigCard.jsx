import React, { useMemo } from 'react';
import {
  Code,
  Layers,
  Server,
  Database,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  Clock,
  BookOpen,
  Terminal,
  Brain,
  AlertCircle,
  Sparkles,
  ArrowRight,
  Target,
  Smartphone,
  CheckCircle,
  Flame,
  Zap,
  Briefcase,
  FileText,
} from 'lucide-react';

const CODING_LANGUAGES = [
  { id: 'javascript', label: 'JavaScript (Node.js)', ext: '.js' },
  { id: 'python', label: 'Python 3', ext: '.py' },
  { id: 'java', label: 'Java 17+', ext: '.java' },
  { id: 'cpp', label: 'C++', ext: '.cpp' },
  { id: 'go', label: 'Go (Golang)', ext: '.go' },
];

export default function InterviewConfigCard({
  jobPost = null,
  jobRole = '',
  requiredSkills = [],
  candidateSkills = [],
  candidateProjects = [],
  codingLanguage = 'javascript',
  onSelectCodingLanguage,
  roleFit = null,
  loadingFit = false,
  onStartInterview,
  loading = false,
  error = '',
}) {
  const displayTitle = jobPost?.title || jobRole || 'Software Engineer';
  const displayDept = jobPost?.domain || jobPost?.department || 'Engineering';
  const displayDesc = jobPost?.description || '';
  const displayRequiredSkills =
    jobPost?.required_skills && jobPost.required_skills.length > 0
      ? jobPost.required_skills
      : requiredSkills.length > 0
      ? requiredSkills
      : ['Problem Solving', 'Data Structures', 'System Design'];

  const agendaPhases = useMemo(
    () => [
      {
        num: 1,
        title: 'Introduction & CV',
        subtitle: '4 Questions • Background & Projects',
        duration: '5 min',
        icon: BookOpen,
        desc: 'Introduce yourself, key CV project architectures, and engineering motivations.',
        cardClass: 'border-blue-200/80 bg-blue-50/40 text-blue-900',
        badgeClass: 'bg-blue-100/80 text-blue-800',
      },
      {
        num: 2,
        title: 'Core Technical',
        subtitle: '8 Questions • Required Skills Depth',
        duration: '20 min',
        icon: Cpu,
        desc: 'In-depth assessment on language lifecycles, memory, state management, and query optimization.',
        cardClass: 'border-indigo-200/80 bg-indigo-50/40 text-indigo-900',
        badgeClass: 'bg-indigo-100/80 text-indigo-800',
      },
      {
        num: 3,
        title: 'System Design',
        subtitle: '3 Questions • Distributed Architecture',
        duration: '15 min',
        icon: Sparkles,
        desc: 'Dedicated distributed architecture, microservices, caching, sharding, and resilience trade-offs.',
        cardClass: 'border-cyan-200/80 bg-cyan-50/40 text-cyan-900',
        badgeClass: 'bg-cyan-100/80 text-cyan-800',
      },
      {
        num: 4,
        title: 'Coding Sandbox',
        subtitle: '2 Questions • Live Monaco Sandbox',
        duration: '20 min',
        icon: Code,
        desc: 'Implement optimal algorithmic solutions executed against public and hidden unit test suites.',
        cardClass: 'border-purple-200/80 bg-purple-50/40 text-purple-900',
        badgeClass: 'bg-purple-100/80 text-purple-800',
      },
      {
        num: 5,
        title: 'Behavioral',
        subtitle: '3 Questions • Incident Triage & Team Standards',
        duration: '10 min',
        icon: ShieldCheck,
        desc: 'Situational evaluation of production incident triage, refactoring tech debt, and team consensus.',
        cardClass: 'border-emerald-200/80 bg-emerald-50/40 text-emerald-900',
        badgeClass: 'bg-emerald-100/80 text-emerald-800',
      },
      {
        num: 6,
        title: 'Closing & Culture',
        subtitle: '2 Questions • Career Alignment & Q&A',
        duration: '5 min',
        icon: Target,
        desc: 'Discuss career growth aspirations, team engineering culture preferences, and candidate reflections.',
        cardClass: 'border-slate-200/80 bg-slate-50/40 text-slate-900',
        badgeClass: 'bg-slate-100/80 text-slate-800',
      },
    ],
    []
  );

  const handleStart = () => {
    onStartInterview?.({
      jobRole: displayTitle,
      codingLanguage,
    });
  };

  return (
    <div className="space-y-6">
      {/* Main Job & Candidate Calibration Card */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-7 shadow-xs">
        {/* Header Section */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-700 text-white shadow-xs">
              <Briefcase className="h-6 w-6 sm:h-7 sm:w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200/80">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  Target Position
                </span>
                <span className="text-xs text-slate-400 font-medium">• {displayDept}</span>
              </div>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                {displayTitle}
              </h2>
              {displayDesc && (
                <p className="mt-2 max-w-2xl text-xs sm:text-sm text-slate-600 line-clamp-2">
                  {displayDesc}
                </p>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 text-right shadow-2xs">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Assessment Duration
            </div>
            <div className="flex items-center justify-end gap-1.5 text-base sm:text-lg font-bold text-slate-900">
              <Clock className="h-4 w-4 text-blue-700" />
              ~55 mins
            </div>
            <div className="text-[10px] text-slate-500 font-medium">4 Structured Stages</div>
          </div>
        </div>

        {/* Required Stack & Matched CV Skills Grid */}
        <div className="grid gap-5 pt-6 md:grid-cols-2">
          {/* Required Job Stack */}
          <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-4 sm:p-5">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
              <Target className="h-4 w-4 text-blue-700" />
              Required Job Stack from Posting
            </div>
            <p className="mt-1 text-xs text-slate-500">
              AI questions will evaluate these specific technologies:
            </p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {displayRequiredSkills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-800"
                >
                  <Sparkles className="h-3 w-3 text-blue-600" />
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Candidate Matched CV Profile */}
          <div className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-4 sm:p-5">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
              <FileText className="h-4 w-4 text-emerald-600" />
              Extracted CV Profile & Matched Skills
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Grounded in your resume projects and technical background:
            </p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {candidateSkills.length > 0 ? (
                candidateSkills.slice(0, 8).map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800"
                  >
                    <CheckCircle className="h-3 w-3 text-emerald-600" />
                    {skill}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400 italic">
                  Calibrated to standard {displayTitle} competencies
                </span>
              )}
            </div>
            {candidateProjects && candidateProjects.length > 0 && (
              <div className="mt-3 border-t border-slate-200/60 pt-2 text-xs text-slate-600">
                <span className="font-semibold text-slate-800">Featured Project:</span>{' '}
                {candidateProjects[0]?.title || candidateProjects[0]?.name || 'Production Architecture'}
              </div>
            )}
          </div>
        </div>

        {/* 4-Phase Interview Agenda */}
        <div className="mt-7 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              4-Phase Live Interview Agenda
            </h3>
            <span className="text-xs text-slate-500 font-medium">
              Real-Time AI Question & Multi-Dimensional Rubric Engine
            </span>
          </div>

          <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
            {agendaPhases.map((phase) => {
              const Icon = phase.icon;
              return (
                <div
                  key={phase.num}
                  className={`rounded-xl border p-4 transition ${phase.cardClass}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-white text-xs font-bold text-slate-900 border border-slate-200/80 shadow-2xs">
                      {phase.num}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-600">
                      {phase.duration}
                    </span>
                  </div>
                  <div className="mt-3 font-bold text-slate-900 text-sm">
                    {phase.title}
                  </div>
                  <div className="text-[11px] font-medium text-slate-600 mt-0.5">
                    {phase.subtitle}
                  </div>
                  <p className="mt-2 text-[11px] text-slate-500 leading-relaxed line-clamp-3">
                    {phase.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Coding Sandbox Language Selection */}
        <div className="mt-7 rounded-xl border border-slate-200/80 bg-slate-50/60 p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
                <Terminal className="h-4 w-4 text-blue-700" />
                Preferred Coding Sandbox Language
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Choose the programming language for Phase 3 algorithmic coding challenges:
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {CODING_LANGUAGES.map((lang) => {
                const isSelected = codingLanguage === lang.id;
                return (
                  <button
                    key={lang.id}
                    type="button"
                    onClick={() => onSelectCodingLanguage?.(lang.id)}
                    className={`rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
                      isSelected
                        ? 'bg-blue-700 text-white shadow-xs'
                        : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-2xs'
                    }`}
                  >
                    {lang.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mt-6 flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 shadow-xs">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {/* CTA Launch Section */}
        <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-6">
          <div className="text-xs text-slate-500">
            Microphone & Camera permissions will be requested upon entering the live room.
          </div>

          <button
            type="button"
            onClick={handleStart}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-700 hover:bg-blue-800 px-7 py-3 text-xs sm:text-sm font-semibold text-white shadow-xs transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Launching Session...</span>
              </>
            ) : (
              <>
                <span>Start Live Interview for {displayTitle}</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

