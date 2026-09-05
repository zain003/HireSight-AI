import React, { useMemo } from 'react';
import {
  Code,
  Layers,
  Server,
  Database,
  Cpu,
  ShieldCheck,
  Compass,
  CheckCircle2,
  Clock,
  BookOpen,
  Terminal,
  Brain,
  AlertCircle,
  Sparkles,
  ArrowRight,
  Target,
} from 'lucide-react';

const ROLE_ICONS = {
  frontend_engineer: LayoutIcon,
  backend_engineer: Server,
  fullstack_engineer: Layers,
  devops_engineer: Terminal,
  data_engineer: Database,
  ml_engineer: Brain,
  qa_automation_engineer: ShieldCheck,
};

function LayoutIcon(props) {
  return <Code {...props} />;
}

const SENIORITY_LEVELS = [
  { id: 'entry', label: 'Entry-Level', experience: '0–2 yrs', desc: 'Core fundamentals & guided problem-solving' },
  { id: 'mid', label: 'Mid-Level', experience: '2–5 yrs', desc: 'Autonomous system design & clean implementations' },
  { id: 'senior', label: 'Senior', experience: '5–8 yrs', desc: 'Architecture, trade-offs & complex optimization' },
  { id: 'lead', label: 'Lead / Principal', experience: '8+ yrs', desc: 'High-scale strategy, reliability & leadership' },
];

const CODING_LANGUAGES = [
  { id: 'python', label: 'Python', ext: '.py', popular: true },
  { id: 'javascript', label: 'JavaScript (Node.js)', ext: '.js', popular: true },
  { id: 'java', label: 'Java', ext: '.java', popular: false },
  { id: 'cpp', label: 'C++', ext: '.cpp', popular: false },
  { id: 'c', label: 'C', ext: '.c', popular: false },
];

export default function InterviewConfigCard({
  roles = [],
  selectedRoleId,
  onSelectRole,
  seniority = 'mid',
  onSelectSeniority,
  codingLanguage = 'python',
  onSelectCodingLanguage,
  roleFit = null,
  loadingFit = false,
  onStartInterview,
  loading = false,
  error = '',
}) {
  const selectedRole = useMemo(() => {
    return roles.find((r) => r.role_id === selectedRoleId) || roles[0] || null;
  }, [roles, selectedRoleId]);

  const agendaStages = useMemo(() => {
    let techDuration = '15 min';
    let codeDuration = '20 min';
    let totalEst = '45–50 min';

    if (seniority === 'senior' || seniority === 'lead') {
      techDuration = '20 min';
      codeDuration = '25 min';
      totalEst = '55–60 min';
    } else if (seniority === 'entry') {
      techDuration = '12 min';
      codeDuration = '15 min';
      totalEst = '40–45 min';
    }

    return [
      {
        stage: 1,
        title: 'Introduction & Background',
        type: 'Icebreaker',
        duration: '5 min',
        questions: '2 questions',
        desc: 'Candidate background, communication style & career journey',
        icon: Compass,
        color: 'text-sky-400',
        bg: 'bg-sky-500/10 border-sky-500/20',
      },
      {
        stage: 2,
        title: 'Technical Domain Evaluation',
        type: 'Rubric Graded',
        duration: techDuration,
        questions: '7 questions',
        desc: `${selectedRole?.display_name || 'Role'} core competencies & system concepts`,
        icon: BookOpen,
        color: 'text-indigo-400',
        bg: 'bg-indigo-500/10 border-indigo-500/20',
      },
      {
        stage: 3,
        title: 'Coding & Algorithmic Sandbox',
        type: 'Live Execution',
        duration: codeDuration,
        questions: '3 challenges',
        desc: `Sandboxed execution in ${codingLanguage.toUpperCase()} with public & hidden tests`,
        icon: Terminal,
        color: 'text-emerald-400',
        bg: 'bg-emerald-500/10 border-emerald-500/20',
      },
      {
        stage: 4,
        title: 'Behavioral & Situational Closing',
        type: 'Multimodal',
        duration: '10 min',
        questions: '8 questions',
        desc: 'STAR framework behavioral scenarios & CV-anchored deep dives',
        icon: Brain,
        color: 'text-amber-400',
        bg: 'bg-amber-500/10 border-amber-500/20',
      },
    ];
  }, [seniority, selectedRole, codingLanguage]);

  const fitPercent = useMemo(() => {
    if (!roleFit || typeof roleFit.role_fit_score !== 'number') return null;
    return Math.round(roleFit.role_fit_score * 100);
  }, [roleFit]);

  return (
    <div className="space-y-8">
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-950/40 p-4 text-sm text-red-200 backdrop-blur-sm">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
          <div>
            <p className="font-medium text-red-100">Setup Notification</p>
            <p className="mt-0.5 text-xs text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* 1. Target Role Selection */}
      <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-4">
          <div>
            <h3 className="flex items-center gap-2 text-lg font-bold text-white">
              <Target className="h-5 w-5 text-indigo-400" />
              1. Select Target Job Role
            </h3>
            <p className="text-xs text-slate-400">
              Choose the standardized engineering role for which questions and grading rubrics will be generated.
            </p>
          </div>
          {selectedRole && (
            <span className="rounded-full border border-indigo-400/30 bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-200">
              {selectedRole.display_name}
            </span>
          )}
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {roles.map((r) => {
            const isSelected = r.role_id === selectedRoleId;
            const Icon = ROLE_ICONS[r.role_id] || Layers;
            return (
              <button
                key={r.role_id}
                type="button"
                onClick={() => onSelectRole?.(r.role_id)}
                className={`group relative flex flex-col justify-between rounded-xl border p-4 text-left transition-all duration-200 ${
                  isSelected
                    ? 'border-indigo-400 bg-indigo-950/40 shadow-lg shadow-indigo-950/50 ring-2 ring-indigo-400/40'
                    : 'border-white/10 bg-slate-950/40 hover:border-white/20 hover:bg-white/5'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-lg transition ${
                        isSelected ? 'bg-indigo-500 text-white shadow-md' : 'bg-white/10 text-slate-300 group-hover:text-white'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    {isSelected && <CheckCircle2 className="h-5 w-5 text-indigo-400" />}
                  </div>

                  <p className="mt-3 text-sm font-semibold text-white group-hover:text-indigo-200">
                    {r.display_name}
                  </p>
                  <p className="mt-1 text-[11px] capitalize text-slate-400">
                    Default seniority: <span className="font-medium text-slate-300">{r.inferred_seniority}</span>
                  </p>
                </div>

                <div className="mt-3 flex flex-wrap gap-1">
                  {r.competency_areas?.slice(0, 2).map((comp) => (
                    <span
                      key={comp}
                      className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] font-medium text-slate-300"
                    >
                      {comp}
                    </span>
                  ))}
                  {(r.competency_areas?.length || 0) > 2 && (
                    <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-400">
                      +{r.competency_areas.length - 2}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Role Competency Matrix Deep-Dive */}
        {selectedRole && (
          <div className="mt-5 rounded-xl border border-white/10 bg-slate-950/60 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Evaluated Competency Clusters ({selectedRole.competency_areas?.length || 0})
              </span>
              {loadingFit ? (
                <span className="flex items-center gap-1.5 text-xs text-indigo-300">
                  <span className="h-3 w-3 animate-spin rounded-full border border-indigo-400 border-t-transparent" />
                  Calculating role fit...
                </span>
              ) : fitPercent !== null ? (
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                    fitPercent >= 75
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : fitPercent >= 50
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-red-500/20 text-red-300 border border-red-500/30'
                  }`}
                >
                  <Sparkles className="h-3 w-3" />
                  Skill Match: {fitPercent}%
                </span>
              ) : null}
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {selectedRole.competency_areas?.map((comp) => {
                const isMatched = roleFit?.matched_skills?.some(
                  (s) => s.toLowerCase() === comp.toLowerCase()
                );
                return (
                  <span
                    key={comp}
                    className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium ${
                      isMatched
                        ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                        : 'border-white/15 bg-white/5 text-slate-300'
                    }`}
                  >
                    {isMatched && <CheckCircle2 className="h-3 w-3 text-emerald-400" />}
                    {comp}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* 2. Seniority Level & Coding Language Preference */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Seniority Tier Selector */}
        <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
          <h3 className="flex items-center gap-2 text-lg font-bold text-white">
            <Layers className="h-5 w-5 text-indigo-400" />
            2. Seniority Tier / Difficulty
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Calibrates algorithmic complexity, system architecture depth, and grading rubric expectations.
          </p>

          <div className="mt-5 space-y-3">
            {SENIORITY_LEVELS.map((lvl) => {
              const isSelected = seniority === lvl.id;
              return (
                <button
                  key={lvl.id}
                  type="button"
                  onClick={() => onSelectSeniority?.(lvl.id)}
                  className={`flex w-full items-center justify-between rounded-xl border p-3.5 text-left transition ${
                    isSelected
                      ? 'border-indigo-400 bg-indigo-950/40 ring-2 ring-indigo-400/40'
                      : 'border-white/10 bg-slate-950/40 hover:border-white/20 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                        isSelected
                          ? 'border-indigo-400 bg-indigo-500'
                          : 'border-slate-500 bg-transparent'
                      }`}
                    >
                      {isSelected && <div className="h-2 w-2 rounded-full bg-white" />}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{lvl.label}</p>
                      <p className="text-xs text-slate-400">{lvl.desc}</p>
                    </div>
                  </div>
                  <span className="shrink-0 rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs font-mono text-indigo-300">
                    {lvl.experience}
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        {/* Coding Language Preference */}
        <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
          <h3 className="flex items-center gap-2 text-lg font-bold text-white">
            <Terminal className="h-5 w-5 text-emerald-400" />
            3. Coding Assessment Language
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Selected language for Stage 3 sandbox execution with isolated subprocess test verification.
          </p>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {CODING_LANGUAGES.map((lang) => {
              const isSelected = codingLanguage === lang.id;
              return (
                <button
                  key={lang.id}
                  type="button"
                  onClick={() => onSelectCodingLanguage?.(lang.id)}
                  className={`flex items-center justify-between rounded-xl border p-3.5 text-left transition ${
                    isSelected
                      ? 'border-emerald-400 bg-emerald-950/30 ring-2 ring-emerald-400/40'
                      : 'border-white/10 bg-slate-950/40 hover:border-white/20 hover:bg-white/5'
                  }`}
                >
                  <div>
                    <p className="text-sm font-semibold text-white">{lang.label}</p>
                    <span className="text-[11px] font-mono text-slate-400">{lang.ext} file format</span>
                  </div>
                  {isSelected && <CheckCircle2 className="h-5 w-5 text-emerald-400" />}
                </button>
              );
            })}
          </div>

          <div className="mt-5 rounded-xl border border-white/10 bg-slate-950/40 p-4">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Clock className="h-4 w-4 text-indigo-300" />
              <span>
                Sandbox Limits: <strong className="text-white">5s compile</strong> · <strong className="text-white">3s per test</strong> · <strong className="text-white">10KB stdout cap</strong>
              </span>
            </div>
          </div>
        </section>
      </div>

      {/* 3. Structured Interview Agenda Preview */}
      <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-4">
          <div>
            <h3 className="flex items-center gap-2 text-lg font-bold text-white">
              <Clock className="h-5 w-5 text-amber-400" />
              4. Structured Interview Agenda Preview
            </h3>
            <p className="text-xs text-slate-400">
              Complete 20-question multidimensional evaluation agenda tailored to the {seniority.toUpperCase()} tier.
            </p>
          </div>
          <span className="rounded-full border border-amber-400/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-300">
            20 Questions Total · ~50 min
          </span>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {agendaStages.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.stage}
                className={`relative flex flex-col justify-between rounded-xl border p-4 transition-all ${stage.bg}`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Stage 0{stage.stage}
                    </span>
                    <span className="rounded-md bg-white/10 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                      {stage.type}
                    </span>
                  </div>

                  <div className="mt-3 flex items-center gap-2">
                    <Icon className={`h-5 w-5 ${stage.color}`} />
                    <h4 className="text-sm font-semibold text-white">{stage.title}</h4>
                  </div>

                  <p className="mt-2 text-xs leading-relaxed text-slate-300">
                    {stage.desc}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1 font-mono text-slate-300">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    {stage.duration}
                  </span>
                  <span className="font-semibold text-white">{stage.questions}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. Action / Launch Bar */}
      <div className="sticky bottom-6 z-20 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-indigo-400/30 bg-slate-950/90 p-5 shadow-2xl backdrop-blur-lg">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-indigo-300">
            Configured Assessment
          </p>
          <p className="text-base font-bold text-white">
            {selectedRole?.display_name || 'Engineering Role'} · <span className="capitalize">{seniority}</span> Tier · <span className="uppercase font-mono">{codingLanguage}</span>
          </p>
        </div>

        <button
          type="button"
          disabled={loading || !selectedRoleId}
          onClick={() =>
            onStartInterview?.({
              roleId: selectedRoleId,
              roleDisplayName: selectedRole?.display_name,
              seniority,
              codingLanguage,
            })
          }
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:from-indigo-400 hover:to-violet-500 hover:shadow-indigo-500/40 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Initializing Session...
            </>
          ) : (
            <>
              Start Structured Interview
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
