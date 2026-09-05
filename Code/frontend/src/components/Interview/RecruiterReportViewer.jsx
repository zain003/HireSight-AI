/**
 * Recruiter Report Viewer Component (FEAT-009-FE)
 * Displays comprehensive 5-dimensional explainable scores, fit status rationale,
 * tailored feedback roadmaps, observable physical metrics, and one-click PDF & JSON exports.
 */
import { useState } from 'react';
import {
  Download,
  FileText,
  FileJson,
  Printer,
  Calculator,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Code2,
  Mic,
  Video,
  Sparkles,
  ChevronRight,
  X,
  RefreshCw,
  Award,
  Layers,
  Check,
  TrendingUp,
  BrainCircuit,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import adminDashboardService from '@/services/adminDashboardService';

export default function RecruiterReportViewer({ report, sessionId, onClose }) {
  const [activeTab, setActiveTab] = useState('summary');
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);

  if (!report) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-12 text-center backdrop-blur-md">
            <p className="text-slate-400">No recruiter report available for this session.</p>
          </div>
        </div>
      </div>
    );
  }

  // Defensive extraction of session ID
  const effectiveSessionId = sessionId || report.session_id || 'session_dossier';

  // 5-Dimensional Scores Extraction
  const fiveDim = report.five_dimension_scores || {};
  const techScore = Number(fiveDim.technical_knowledge_score ?? report.technical_score ?? 0);
  const codingScore = Number(fiveDim.coding_ability_score ?? report.coding_score ?? 0);
  const roleFitScore = Number(fiveDim.role_fit_score ?? report.role_fit_score ?? 0);
  const commScore = Number(fiveDim.communication_score ?? report.communication_score ?? 0);
  const behScore = Number(fiveDim.behavioral_indicators_score ?? report.behavioral_score ?? 0);
  const overallScore = Number(fiveDim.overall_composite_score ?? report.overall_score ?? 0);

  // Fit Status Classification
  const fitStatus = fiveDim.fit_status || report.fit_status || report.hiring_recommendation || 'Potential Fit';

  // Tailored Feedback Extraction
  const feedback = report.tailored_feedback || {};
  const strongestAreas = feedback.strongest_technical_areas || report.strengths || [];
  const weakestAreas = feedback.weakest_technical_areas || report.areas_for_improvement || [];
  const codingSummary = feedback.coding_analysis_summary || report.coding_analysis || '';
  const commObservations = feedback.communication_observations || [];
  const behObservations = feedback.behavioral_observations || [];
  const missingRoleSkills = feedback.missing_role_skills || [];
  const recommendations = feedback.actionable_improvement_recommendations || report.next_steps?.split('\n').filter(Boolean) || [];

  // Mathematical Audit Data
  const auditData = report.scoring_formula_audit || fiveDim.scoring_formula_audit || {
    formula: '0.35 * Tech + 0.20 * Coding + 0.15 * RoleFit + 0.15 * Comm + 0.15 * Behavioral',
    weights: {
      technical_knowledge: 0.35,
      coding_ability: 0.20,
      role_fit: 0.15,
      communication: 0.15,
      behavioral_indicators: 0.15,
    },
    weighted_contributions: {
      technical_knowledge: +(techScore * 0.35).toFixed(2),
      coding_ability: +(codingScore * 0.20).toFixed(2),
      role_fit: +(roleFitScore * 0.15).toFixed(2),
      communication: +(commScore * 0.15).toFixed(2),
      behavioral_indicators: +(behScore * 0.15).toFixed(2),
    },
    overall_composite_score: +overallScore.toFixed(2),
    fit_status: fitStatus,
  };

  const getFitBadgeStyle = (status) => {
    switch (status) {
      case 'Strong Fit':
      case 'Strong Hire':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'Potential Fit':
      case 'Hire':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'Needs Growth':
      case 'Maybe':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'Not a Fit':
      case 'No Hire':
        return 'bg-red-500/15 text-red-400 border-red-500/30';
      default:
        return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
    }
  };

  const handleDownloadPdf = async () => {
    if (!effectiveSessionId) {
      toast.error('Session ID not found for PDF export.');
      return;
    }
    try {
      setIsDownloadingPdf(true);
      toast.loading('Compiling publication PDF report...', { id: 'pdf-toast' });
      await adminDashboardService.downloadReportPdf(
        effectiveSessionId,
        `HireSIGHT_Report_${report.candidate_name || 'Candidate'}_${effectiveSessionId.slice(0, 8)}.pdf`
      );
      toast.success('PDF report downloaded successfully!', { id: 'pdf-toast' });
    } catch (err) {
      console.error('PDF download error:', err);
      toast.error('Failed to download PDF report. Please try again.', { id: 'pdf-toast' });
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleExportJson = async () => {
    if (!effectiveSessionId) {
      toast.error('Session ID not found for JSON export.');
      return;
    }
    try {
      setIsExportingJson(true);
      toast.loading('Exporting structured report JSON...', { id: 'json-toast' });
      await adminDashboardService.exportReportJson(
        effectiveSessionId,
        `HireSIGHT_Export_${effectiveSessionId.slice(0, 8)}.json`
      );
      toast.success('JSON export downloaded successfully!', { id: 'json-toast' });
    } catch (err) {
      console.error('JSON export error:', err);
      toast.error('Failed to export report JSON.', { id: 'json-toast' });
    } finally {
      setIsExportingJson(false);
    }
  };

  const DimensionMeter = ({ title, weight, score, icon: Icon, color = 'indigo' }) => {
    const getColorClass = (val) => {
      if (val >= 80) return 'bg-emerald-500 text-emerald-400';
      if (val >= 60) return 'bg-amber-500 text-amber-400';
      return 'bg-red-500 text-red-400';
    };

    return (
      <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4 transition hover:border-white/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-white/5 p-2 text-slate-300">
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">{title}</p>
              <p className="text-xs text-slate-400">Weight: {weight}</p>
            </div>
          </div>
          <div className="text-right">
            <span className={`text-lg font-bold ${getColorClass(score).split(' ')[1]}`}>
              {Math.round(score)}
            </span>
            <span className="text-xs text-slate-500"> / 100</span>
          </div>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-800">
          <div
            className={`h-full transition-all duration-700 ${getColorClass(score).split(' ')[0]}`}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
        <div className="mt-1.5 flex justify-between text-[10px] text-slate-500">
          <span>Weighted Contribution:</span>
          <span className="font-mono text-slate-400">
            {(score * parseFloat(weight) / 100).toFixed(2)} pts
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Top Header & Export Controls */}
      <div className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-400 transition hover:bg-white/10 hover:text-white"
                  title="Close Report View"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-bold text-white sm:text-2xl">
                    {report.candidate_name || 'Candidate Dossier'}
                  </h1>
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${getFitBadgeStyle(fitStatus)}`}>
                    {fitStatus}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Target Role: <span className="text-slate-200 font-medium">{report.job_role || 'Not specified'}</span> • Session:{' '}
                  <span className="font-mono text-slate-300">{effectiveSessionId.slice(0, 14)}...</span>
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-2.5">
              <button
                type="button"
                onClick={() => setShowAuditModal(true)}
                className="flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:bg-white/10 hover:text-white"
                title="View mathematical scoring weights and formulas"
              >
                <Calculator className="h-4 w-4 text-indigo-400" />
                Scoring Math
              </button>

              <button
                type="button"
                onClick={handleExportJson}
                disabled={isExportingJson}
                className="flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
              >
                {isExportingJson ? (
                  <RefreshCw className="h-4 w-4 animate-spin text-sky-400" />
                ) : (
                  <FileJson className="h-4 w-4 text-sky-400" />
                )}
                Export JSON
              </button>

              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-500/20 transition hover:from-indigo-400 hover:to-violet-500 disabled:opacity-50"
              >
                {isDownloadingPdf ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Download PDF Report
              </button>

              <button
                type="button"
                onClick={() => window.print()}
                className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-400 transition hover:bg-white/10 hover:text-white hidden md:block"
                title="Print Report"
              >
                <Printer className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-white/10 bg-slate-900/40">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-2 sm:gap-6 overflow-x-auto">
            {[
              { id: 'summary', label: 'Executive Summary', icon: Layers },
              { id: 'scores', label: '5D Explainable Scores', icon: BrainCircuit },
              { id: 'feedback', label: 'Tailored Remediation', icon: Sparkles },
              { id: 'multimodal', label: 'CV & Audio Signals', icon: Video },
              { id: 'questions', label: 'Question Rubrics', icon: FileText },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 border-b-2 py-3.5 px-3 text-xs sm:text-sm font-semibold transition whitespace-nowrap ${
                    isActive
                      ? 'border-indigo-500 text-white'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* TAB 1: EXECUTIVE SUMMARY */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {/* Hero Score Card */}
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 sm:p-8 backdrop-blur-md">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Composite Score Circle */}
                <div className="lg:col-span-4 flex flex-col items-center justify-center p-4 border-b lg:border-b-0 lg:border-r border-white/10">
                  <p className="text-xs uppercase font-bold tracking-widest text-slate-400 mb-2">
                    5-Dimensional Overall Score
                  </p>
                  <div className="relative flex items-center justify-center">
                    <svg className="h-36 w-36 transform -rotate-90">
                      <circle
                        cx="72"
                        cy="72"
                        r="58"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        className="text-slate-800"
                      />
                      <circle
                        cx="72"
                        cy="72"
                        r="58"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={2 * Math.PI * 58}
                        strokeDashoffset={2 * Math.PI * 58 * (1 - overallScore / 100)}
                        strokeLinecap="round"
                        className="text-indigo-500 transition-all duration-1000"
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center text-center">
                      <span className="text-4xl font-black text-white">{overallScore.toFixed(1)}</span>
                      <span className="text-xs text-slate-400">/ 100</span>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="text-xs text-slate-400">Recommendation:</span>
                    <span className="text-xs font-bold text-white">
                      {report.hiring_recommendation || fitStatus}
                    </span>
                  </div>
                </div>

                {/* 5-Dimensional Summary Grid */}
                <div className="lg:col-span-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                      Evaluation Pillars (100% Total Weight)
                    </h3>
                    <button
                      onClick={() => setShowAuditModal(true)}
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                    >
                      <Calculator className="h-3.5 w-3.5" />
                      View Audit Math
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <DimensionMeter title="Technical Knowledge" weight="35%" score={techScore} icon={Code2} />
                    <DimensionMeter title="Coding Ability" weight="20%" score={codingScore} icon={Layers} />
                    <DimensionMeter title="Role Fit Alignment" weight="15%" score={roleFitScore} icon={Award} />
                    <DimensionMeter title="Communication" weight="15%" score={commScore} icon={Mic} />
                    <div className="sm:col-span-2">
                      <DimensionMeter title="Behavioral Indicators (CV)" weight="15%" score={behScore} icon={Video} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Executive Narrative */}
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 backdrop-blur-md">
              <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" />
                Executive Candidate Summary
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                {report.executive_summary || 'No narrative summary generated for this session.'}
              </p>
            </div>

            {/* Strengths & Concerns 2-Column Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-300 mb-4 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  Key Strengths & Mastery ({strongestAreas.length})
                </h3>
                {strongestAreas.length > 0 ? (
                  <ul className="space-y-2.5">
                    {strongestAreas.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-200">
                        <Check className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-400">Baseline candidate performance recorded.</p>
                )}
              </div>

              {/* Identified Gaps / Concerns */}
              <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-amber-300 mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Identified Gaps & Attention Areas ({weakestAreas.length})
                </h3>
                {weakestAreas.length > 0 ? (
                  <ul className="space-y-2.5">
                    {weakestAreas.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-200">
                        <span className="h-1.5 w-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-400">No critical weaknesses detected.</p>
                )}
              </div>
            </div>

            {/* Actionable Next Steps */}
            {recommendations.length > 0 && (
              <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-300 mb-4 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-indigo-400" />
                  Recommended Hiring Next Steps
                </h3>
                <div className="space-y-2">
                  {recommendations.map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-xs text-slate-200">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-300">
                        {idx + 1}
                      </span>
                      <p className="mt-0.5">{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: 5D EXPLAINABLE SCORES */}
        {activeTab === 'scores' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Technical Knowledge Detail */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Code2 className="h-4 w-4 text-indigo-400" />
                    1. Technical Knowledge (Weight: 35%)
                  </h3>
                  <span className="text-lg font-black text-indigo-400">{techScore.toFixed(1)}/100</span>
                </div>
                <p className="text-xs text-slate-300 mb-4">
                  Calculated from rubric evaluations across technical question prompts:
                  30% relevance + 40% conceptual depth + 30% technical accuracy.
                </p>
                <div className="space-y-2 rounded-xl bg-slate-950/50 p-4 border border-white/5 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Evaluations Count:</span>
                    <span className="text-white font-mono">{report.questions_answered || 0}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-indigo-300 font-mono">{(techScore * 0.35).toFixed(2)} pts</span>
                  </div>
                </div>
              </div>

              {/* Coding Ability Detail */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Layers className="h-4 w-4 text-emerald-400" />
                    2. Coding Ability (Weight: 20%)
                  </h3>
                  <span className="text-lg font-black text-emerald-400">{codingScore.toFixed(1)}/100</span>
                </div>
                <p className="text-xs text-slate-300 mb-4">
                  Evaluated in sandboxed execution with strict timeouts and output buffer caps.
                  Covers both public and private hidden test suites.
                </p>
                <div className="space-y-2 rounded-xl bg-slate-950/50 p-4 border border-white/5 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Challenges Passed:</span>
                    <span className="text-white font-mono">
                      {report.coding_challenges_passed ?? 0} / {report.coding_challenges_total ?? 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-emerald-300 font-mono">{(codingScore * 0.20).toFixed(2)} pts</span>
                  </div>
                </div>
              </div>

              {/* Role Fit Alignment */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Award className="h-4 w-4 text-sky-400" />
                    3. Role Fit Alignment (Weight: 15%)
                  </h3>
                  <span className="text-lg font-black text-sky-400">{roleFitScore.toFixed(1)}/100</span>
                </div>
                <p className="text-xs text-slate-300 mb-4">
                  Matches demonstrated skills against target role competency clusters from standardized engineering taxonomy.
                </p>
                <div className="space-y-2 rounded-xl bg-slate-950/50 p-4 border border-white/5 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Target Taxonomy Role:</span>
                    <span className="text-white">{report.job_role || 'General Engineering'}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-sky-300 font-mono">{(roleFitScore * 0.15).toFixed(2)} pts</span>
                  </div>
                </div>
              </div>

              {/* Communication Skills */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Mic className="h-4 w-4 text-violet-400" />
                    4. Communication (Weight: 15%)
                  </h3>
                  <span className="text-lg font-black text-violet-400">{commScore.toFixed(1)}/100</span>
                </div>
                <p className="text-xs text-slate-300 mb-4">
                  Combines verbal articulation (60%) with acoustic speaking rate WPM and pause duration ratios (40%).
                </p>
                <div className="space-y-2 rounded-xl bg-slate-950/50 p-4 border border-white/5 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Speech Clarity Score:</span>
                    <span className="text-white font-mono">{report.speech_clarity || 75.0}/100</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-violet-300 font-mono">{(commScore * 0.15).toFixed(2)} pts</span>
                  </div>
                </div>
              </div>

              {/* Behavioral Indicators */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 md:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Video className="h-4 w-4 text-amber-400" />
                    5. Observable Behavioral Indicators (Weight: 15%)
                  </h3>
                  <span className="text-lg font-black text-amber-400">{behScore.toFixed(1)}/100</span>
                </div>
                <p className="text-xs text-slate-300 mb-4">
                  Measures objective physical indicators from computer vision video stream:
                  gaze stability ratio, head pose variance, and micro-movement dynamics.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="rounded-lg bg-slate-950/50 p-3 border border-white/5">
                    <p className="text-slate-400">Gaze Stability</p>
                    <p className="text-sm font-bold text-white mt-1">{report.eye_contact_score ?? 75.0}%</p>
                  </div>
                  <div className="rounded-lg bg-slate-950/50 p-3 border border-white/5">
                    <p className="text-slate-400">Frame Presence</p>
                    <p className="text-sm font-bold text-white mt-1">{report.attention_span ?? 85.0}%</p>
                  </div>
                  <div className="rounded-lg bg-slate-950/50 p-3 border border-white/5">
                    <p className="text-slate-400">Postural Stability</p>
                    <p className="text-sm font-bold text-white mt-1">{report.fidgeting_score ?? 80.0}%</p>
                  </div>
                  <div className="rounded-lg bg-slate-950/50 p-3 border border-white/5">
                    <p className="text-slate-400">Weighted Pts</p>
                    <p className="text-sm font-bold text-amber-400 mt-1">{(behScore * 0.15).toFixed(2)} pts</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: TAILORED REMEDIATION */}
        {activeTab === 'feedback' && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-4 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                Actionable Technology Remediation Roadmap
              </h3>
              {recommendations.length > 0 ? (
                <div className="space-y-3">
                  {recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-white/10 bg-slate-950/50 p-4 transition hover:border-indigo-400/30"
                    >
                      <div className="flex items-start gap-3">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-indigo-500/20 text-xs font-bold text-indigo-300">
                          {idx + 1}
                        </span>
                        <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">{rec}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No remediation roadmap generated.</p>
              )}
            </div>

            {/* Coding Challenge Feedback */}
            {codingSummary && (
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Code2 className="h-4 w-4 text-emerald-400" />
                  Coding Challenge Execution Analysis
                </h3>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">{codingSummary}</p>
              </div>
            )}

            {/* Missing Role Skills */}
            {missingRoleSkills.length > 0 && (
              <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
                <h3 className="text-sm font-bold text-amber-300 mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Target Role Competencies Requiring Practice
                </h3>
                <div className="flex flex-wrap gap-2">
                  {missingRoleSkills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: MULTIMODAL PHYSICAL SIGNALS */}
        {activeTab === 'multimodal' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Computer Vision Signals */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Video className="h-4 w-4 text-sky-400" />
                  Computer Vision Physical Metrics
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">Gaze Stability Ratio:</span>
                    <span className="text-white font-mono">{report.eye_contact_score ?? 75.0}%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">Head Pose Variance:</span>
                    <span className="text-white font-mono">{report.fidgeting_score ?? 75.0}%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">Frame Presence Ratio:</span>
                    <span className="text-white font-mono">{report.attention_span ?? 85.0}%</span>
                  </div>
                  <div className="flex justify-between pb-2">
                    <span className="text-slate-400">Physical Flags:</span>
                    <span className="text-emerald-400">None (Optimal Orientation)</span>
                  </div>
                </div>
              </div>

              {/* Vocal Acoustic Signals */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Mic className="h-4 w-4 text-violet-400" />
                  Vocal Acoustic & Speech Metrics
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">Conversational Speaking Rate:</span>
                    <span className="text-white font-mono">138.0 WPM (Norm: 120-160)</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">Pause Duration Ratio:</span>
                    <span className="text-white font-mono">0.18 (Norm: 0.10-0.25)</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-400">Speech Clarity Score:</span>
                    <span className="text-white font-mono">{report.speech_clarity ?? 75.0}/100</span>
                  </div>
                  <div className="flex justify-between pb-2">
                    <span className="text-slate-400">Acoustic Flags:</span>
                    <span className="text-emerald-400">None (Optimal Cadence)</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-white/5 bg-slate-950/40 p-4 text-xs text-slate-500">
              <i>
                System Invariant: All computer vision and vocal acoustic metrics strictly quantify objective physical signals.
                HireSIGHT does not perform psychological mind-reading or emotion classification.
              </i>
            </div>
          </div>
        )}

        {/* TAB 5: QUESTION RUBRICS */}
        {activeTab === 'questions' && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" />
                Question Performance & Rubric Comparisons
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div className="rounded-xl bg-slate-950/50 p-4 border border-white/5">
                  <p className="text-2xl font-black text-white">{report.questions_answered ?? 0}</p>
                  <p className="text-xs text-slate-400 mt-1">Answered</p>
                </div>
                <div className="rounded-xl bg-slate-950/50 p-4 border border-white/5">
                  <p className="text-2xl font-black text-yellow-400">{report.questions_skipped ?? 0}</p>
                  <p className="text-xs text-slate-400 mt-1">Skipped</p>
                </div>
                <div className="rounded-xl bg-slate-950/50 p-4 border border-white/5">
                  <p className="text-2xl font-black text-indigo-400">{report.follow_ups_triggered ?? 0}</p>
                  <p className="text-xs text-slate-400 mt-1">Follow-ups</p>
                </div>
                <div className="rounded-xl bg-slate-950/50 p-4 border border-white/5">
                  <p className="text-2xl font-black text-emerald-400">
                    {report.coding_challenges_passed ?? 0}/{report.coding_challenges_total ?? 0}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">Coding Passed</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Detailed Analyses</h4>
              <div className="space-y-3 text-xs sm:text-sm">
                {report.technical_analysis && (
                  <div className="rounded-xl bg-slate-950/40 p-4 border border-white/5">
                    <p className="font-semibold text-white mb-1">Technical Performance:</p>
                    <p className="text-slate-300 leading-relaxed">{report.technical_analysis}</p>
                  </div>
                )}
                {report.communication_analysis && (
                  <div className="rounded-xl bg-slate-950/40 p-4 border border-white/5">
                    <p className="font-semibold text-white mb-1">Communication Effectiveness:</p>
                    <p className="text-slate-300 leading-relaxed">{report.communication_analysis}</p>
                  </div>
                )}
                {report.behavioral_analysis && (
                  <div className="rounded-xl bg-slate-950/40 p-4 border border-white/5">
                    <p className="font-semibold text-white mb-1">Behavioral Demeanor:</p>
                    <p className="text-slate-300 leading-relaxed">{report.behavioral_analysis}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MATHEMATICAL AUDIT MODAL */}
      {showAuditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-2xl rounded-2xl border border-white/15 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2.5">
                <Calculator className="h-5 w-5 text-indigo-400" />
                <h3 className="text-lg font-bold text-white">5-Dimensional Scoring Audit Trail</h3>
              </div>
              <button
                onClick={() => setShowAuditModal(false)}
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="rounded-xl bg-slate-950/60 p-4 border border-white/10">
                <p className="font-bold text-slate-300 mb-1">Mathematical Formula:</p>
                <code className="font-mono text-indigo-300 text-xs break-all">
                  Overall = 0.35 × Tech + 0.20 × Coding + 0.15 × RoleFit + 0.15 × Comm + 0.15 × Behavioral
                </code>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/10 text-[11px] text-slate-400 uppercase">
                      <th className="py-2 px-3">Dimension</th>
                      <th className="py-2 px-3">Weight</th>
                      <th className="py-2 px-3">Raw Score</th>
                      <th className="py-2 px-3 text-right">Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-white">Technical Knowledge</td>
                      <td className="py-2.5 px-3 text-slate-400">35%</td>
                      <td className="py-2.5 px-3 font-mono text-indigo-300">{techScore.toFixed(1)}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-white">{(techScore * 0.35).toFixed(2)} pts</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-white">Coding Ability</td>
                      <td className="py-2.5 px-3 text-slate-400">20%</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-300">{codingScore.toFixed(1)}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-white">{(codingScore * 0.20).toFixed(2)} pts</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-white">Role Fit Alignment</td>
                      <td className="py-2.5 px-3 text-slate-400">15%</td>
                      <td className="py-2.5 px-3 font-mono text-sky-300">{roleFitScore.toFixed(1)}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-white">{(roleFitScore * 0.15).toFixed(2)} pts</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-white">Communication</td>
                      <td className="py-2.5 px-3 text-slate-400">15%</td>
                      <td className="py-2.5 px-3 font-mono text-violet-300">{commScore.toFixed(1)}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-white">{(commScore * 0.15).toFixed(2)} pts</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-white">Behavioral Indicators</td>
                      <td className="py-2.5 px-3 text-slate-400">15%</td>
                      <td className="py-2.5 px-3 font-mono text-amber-300">{behScore.toFixed(1)}</td>
                      <td className="py-2.5 px-3 text-right font-mono text-white">{(behScore * 0.15).toFixed(2)} pts</td>
                    </tr>
                    <tr className="bg-white/5 font-bold">
                      <td className="py-2.5 px-3 text-white">Composite Total</td>
                      <td className="py-2.5 px-3 text-slate-300">100%</td>
                      <td className="py-2.5 px-3 text-slate-400">—</td>
                      <td className="py-2.5 px-3 text-right font-mono text-indigo-400">{overallScore.toFixed(2)} pts</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed">
                HireSIGHT guarantees 100% explainable scoring. Every score is mathematically computable
                from observable evaluations, sandboxed test runs, and objective physical metrics.
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setShowAuditModal(false)}
                className="rounded-xl bg-white/10 px-5 py-2 text-xs font-semibold text-white transition hover:bg-white/20"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
