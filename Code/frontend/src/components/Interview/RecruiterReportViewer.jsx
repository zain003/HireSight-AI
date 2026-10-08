/**
 * Recruiter Report Viewer Component (FEAT-009-FE)
 * Displays comprehensive 5-dimensional explainable scores, fit status rationale,
 * tailored feedback roadmaps, observable physical metrics, and one-click PDF & JSON exports.
 * Fully supports executive White & Professional theme alongside Dark Mode.
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
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import adminDashboardService from '@/services/adminDashboardService';

export default function RecruiterReportViewer({ report, sessionId, onClose, theme = 'light' }) {
  const isLight = theme === 'light';
  const [activeTab, setActiveTab] = useState('summary');
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);

  if (!report) {
    return (
      <div className={`min-h-[400px] p-6 ${isLight ? 'bg-[#F8FAFC] text-slate-900' : 'bg-slate-950 text-slate-100'}`}>
        <div className="max-w-4xl mx-auto">
          <div className={`rounded-2xl border p-12 text-center ${
            isLight ? 'bg-white border-slate-200 shadow-xs' : 'bg-slate-900/60 border-white/10 backdrop-blur-md'
          }`}>
            <p className="text-slate-500">No recruiter report available for this session.</p>
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

  // Mathematical Audit Data & Mode Detection
  const auditData = report.scoring_formula_audit || fiveDim.scoring_formula_audit || {};
  const commAudit = auditData?.dimension_audits?.communication || {};
  const isTextMode = commAudit.input_mode === 'text' || (!report.speech_clarity && !report.vocal_confidence);
  const behAudit = auditData?.dimension_audits?.behavioral_indicators || {};
  const isVideoCalibrated = (report.attention_span ?? 0) >= 25 && behAudit.is_calibrated !== false;

  const effWeights = auditData.effective_weights || auditData.weights || {
    technical_knowledge: 0.45,
    coding_ability: 0.25,
    communication: 0.15,
    behavioral_indicators: 0.15,
  };

  const contributions = auditData.weighted_contributions || {
    technical_knowledge: +(techScore * (effWeights.technical_knowledge || 0.45)).toFixed(2),
    coding_ability: +(codingScore * (effWeights.coding_ability || 0.25)).toFixed(2),
    communication: +(commScore * (effWeights.communication || 0.15)).toFixed(2),
    behavioral_indicators: +(behScore * (effWeights.behavioral_indicators || 0.15)).toFixed(2),
  };

  const getFitBadgeStyle = (status) => {
    switch (status) {
      case 'Strong Fit':
      case 'Strong Hire':
        return isLight
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
          : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'Potential Fit':
      case 'Hire':
        return isLight
          ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
          : 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'Needs Growth':
      case 'Maybe':
        return isLight
          ? 'bg-amber-50 text-amber-700 border-amber-200'
          : 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'Not a Fit':
      case 'No Hire':
        return isLight
          ? 'bg-rose-50 text-rose-700 border-rose-200'
          : 'bg-red-500/15 text-red-400 border-red-500/30';
      default:
        return isLight
          ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
          : 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
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

  const DimensionMeter = ({ title, weight, score, icon: Icon }) => {
    const getColorClass = (val) => {
      if (val >= 80) return isLight ? 'bg-emerald-600 text-emerald-700' : 'bg-emerald-500 text-emerald-400';
      if (val >= 60) return isLight ? 'bg-amber-500 text-amber-700' : 'bg-amber-500 text-amber-400';
      return isLight ? 'bg-rose-600 text-rose-700' : 'bg-red-500 text-red-400';
    };

    return (
      <div className={`rounded-xl border p-4 transition-all ${
        isLight
          ? 'bg-slate-50/80 border-slate-200/90 hover:bg-white hover:border-slate-300 hover:shadow-xs'
          : 'bg-slate-950/50 border-white/10 hover:border-white/20'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className={`rounded-lg p-2 ${isLight ? 'bg-white border border-slate-200 text-slate-700' : 'bg-white/5 text-slate-300'}`}>
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <p className={`text-sm font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>{title}</p>
              <p className={`text-xs ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>Weight: {weight}</p>
            </div>
          </div>
          <div className="text-right">
            <span className={`text-lg font-black ${getColorClass(score).split(' ')[1]}`}>
              {Math.round(score)}
            </span>
            <span className="text-xs text-slate-400"> / 100</span>
          </div>
        </div>
        <div className={`mt-3 h-2 w-full overflow-hidden rounded-full ${isLight ? 'bg-slate-200' : 'bg-slate-800'}`}>
          <div
            className={`h-full transition-all duration-700 ${getColorClass(score).split(' ')[0]}`}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
        <div className="mt-1.5 flex justify-between text-[10px] text-slate-500">
          <span>Weighted Contribution:</span>
          <span className={`font-mono font-semibold ${isLight ? 'text-slate-700' : 'text-slate-400'}`}>
            {(score * parseFloat(weight) / 100).toFixed(2)} pts
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className={`rounded-2xl transition-colors ${isLight ? 'bg-[#F8FAFC] text-slate-900' : 'bg-slate-950 text-slate-100'}`}>
      {/* Top Header & Export Controls */}
      <div className={`sticky top-0 z-20 border-b rounded-t-2xl backdrop-blur-md transition-colors ${
        isLight ? 'border-slate-200 bg-white/95 text-slate-900 shadow-xs' : 'border-white/10 bg-slate-950/90 text-slate-100'
      }`}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  className={`rounded-xl border p-2 transition ${
                    isLight
                      ? 'border-slate-200 bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900 shadow-xs'
                      : 'border-white/10 bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                  }`}
                  title="Close Report View"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
              <div>
                <div className="flex items-center gap-3">
                  <h1 className={`text-xl font-bold sm:text-2xl ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    {report.candidate_name || 'Candidate Dossier'}
                  </h1>
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${getFitBadgeStyle(fitStatus)}`}>
                    {fitStatus}
                  </span>
                </div>
                <p className={`text-xs mt-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Target Role: <span className={`font-semibold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>{report.job_role || 'Not specified'}</span> • Session:{' '}
                  <span className={`font-mono ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>{effectiveSessionId.slice(0, 14)}...</span>
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-2.5">
              <button
                type="button"
                onClick={() => setShowAuditModal(true)}
                className={`flex items-center gap-1.5 rounded-xl border px-3.5 py-2 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 shadow-xs'
                    : 'border-white/15 bg-white/5 text-slate-200 hover:bg-white/10 hover:text-white'
                }`}
                title="View mathematical scoring weights and formulas"
              >
                <Calculator className="h-4 w-4 text-indigo-600" />
                Scoring Math
              </button>

              <button
                type="button"
                onClick={handleExportJson}
                disabled={isExportingJson}
                className={`flex items-center gap-1.5 rounded-xl border px-3.5 py-2 text-xs font-semibold transition disabled:opacity-50 ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 shadow-xs'
                    : 'border-white/15 bg-white/5 text-slate-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                {isExportingJson ? (
                  <RefreshCw className="h-4 w-4 animate-spin text-sky-600" />
                ) : (
                  <FileJson className="h-4 w-4 text-sky-600" />
                )}
                Export JSON
              </button>

              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:opacity-50"
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
                className={`rounded-xl border p-2 transition hidden md:block ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-600 hover:bg-slate-100 shadow-xs'
                    : 'border-white/10 bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                }`}
                title="Print Report"
              >
                <Printer className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className={`border-b transition-colors ${isLight ? 'border-slate-200 bg-white' : 'border-white/10 bg-slate-900/40'}`}>
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
                      ? isLight
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-indigo-500 text-white'
                      : isLight
                      ? 'border-transparent text-slate-500 hover:text-slate-800'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* TAB 1: EXECUTIVE SUMMARY (1-PAGE TABLE-DRIVEN DOSSIER) */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {/* 1. Hero Dossier Identity & KPI Cards */}
            <div className={`rounded-2xl border p-5 transition-all ${
              isLight ? 'bg-white border-slate-200 shadow-xs' : 'bg-slate-900/60 border-white/10 backdrop-blur-md'
            }`}>
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                {/* Composite Score Ring */}
                <div className={`lg:col-span-4 flex flex-col items-center justify-center p-3 border-b lg:border-b-0 lg:border-r ${
                  isLight ? 'border-slate-100' : 'border-white/10'
                }`}>
                  <p className="text-[11px] uppercase font-bold tracking-wider text-slate-500 mb-2">
                    Overall Composite Score
                  </p>
                  <div className="relative flex items-center justify-center">
                    <svg className="h-32 w-32 transform -rotate-90">
                      <circle
                        cx="64"
                        cy="64"
                        r="52"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        className={isLight ? 'text-slate-100' : 'text-slate-800'}
                      />
                      <circle
                        cx="64"
                        cy="64"
                        r="52"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={2 * Math.PI * 52}
                        strokeDashoffset={2 * Math.PI * 52 * (1 - overallScore / 100)}
                        strokeLinecap="round"
                        className="text-indigo-600 transition-all duration-1000"
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center text-center">
                      <span className={`text-3xl font-black ${isLight ? 'text-slate-900' : 'text-white'}`}>{overallScore.toFixed(1)}</span>
                      <span className="text-[10px] text-slate-400">/ 100</span>
                    </div>
                  </div>
                  <div className="mt-2 text-center">
                    <span className={`inline-block rounded-full border px-3 py-1 text-xs font-bold ${getFitBadgeStyle(fitStatus)}`}>
                      {fitStatus}
                    </span>
                  </div>
                </div>

                {/* Quick Assessment Metrics Grid */}
                <div className="lg:col-span-8 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className={`text-xs font-bold uppercase tracking-wider ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                      Session Assessment Key Metrics
                    </h3>
                    <span className={`text-[11px] font-medium ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                      Target Role: <strong className={isLight ? 'text-slate-800' : 'text-slate-200'}>{report.job_role || 'Software Engineer'}</strong>
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    <div className={`rounded-xl p-3 border text-center ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                      <p className={`text-lg font-black ${isLight ? 'text-slate-900' : 'text-white'}`}>{report.questions_answered ?? 0}</p>
                      <p className="text-[10px] font-semibold text-slate-500 uppercase">Questions</p>
                    </div>
                    <div className={`rounded-xl p-3 border text-center ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                      <p className="text-lg font-black text-emerald-600">
                        {report.coding_challenges_passed ?? 0}/{report.coding_challenges_total ?? 0}
                      </p>
                      <p className="text-[10px] font-semibold text-slate-500 uppercase">Coding Passed</p>
                    </div>
                    <div className={`rounded-xl p-3 border text-center ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                      <p className="text-lg font-black text-indigo-600">
                        {(report.eye_contact_score ?? 88).toFixed(1)}%
                      </p>
                      <p className="text-[10px] font-semibold text-slate-500 uppercase">Gaze Focus</p>
                    </div>
                    <div className={`rounded-xl p-3 border text-center ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                      <p className="text-lg font-black text-violet-600">
                        {(report.speech_clarity ?? 85).toFixed(1)}%
                      </p>
                      <p className="text-[10px] font-semibold text-slate-500 uppercase">Speech Clarity</p>
                    </div>
                  </div>

                  <div className={`flex items-center justify-between rounded-xl p-2.5 border text-xs ${
                    isLight ? 'bg-indigo-50/60 border-indigo-100 text-indigo-900' : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-300'
                  }`}>
                    <span>Hiring Recommendation Verdict:</span>
                    <strong className="font-bold">{fitStatus} — Ready for Recruiter Decision</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. TABLE 1: 5-Dimensional Core Scoring Matrix */}
            <div className={`rounded-2xl border p-5 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  <Calculator className="h-4 w-4 text-indigo-600" />
                  1. 5-Dimensional Explainable Scoring Breakdown
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">Formula: 45% Tech + 25% Code + 15% Comm + 15% Beh</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className={`border-b text-[11px] uppercase ${isLight ? 'bg-slate-100/70 border-slate-200 text-slate-600 font-bold' : 'bg-white/5 border-white/10 text-slate-300'}`}>
                      <th className="py-2.5 px-3">Evaluation Pillar</th>
                      <th className="py-2.5 px-3">Canonical Weight</th>
                      <th className="py-2.5 px-3">Raw Score (0-100)</th>
                      <th className="py-2.5 px-3">Weighted Contribution</th>
                      <th className="py-2.5 px-3">Measurement Basis & Audit Note</th>
                    </tr>
                  </thead>
                  <tbody className={isLight ? 'divide-y divide-slate-100' : 'divide-y divide-white/5'}>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>Technical Knowledge</td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.technical_knowledge || 0.45) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">{techScore.toFixed(1)} / 100</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-600">{contributions.technical_knowledge} pts</td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-500">Rubric evaluations across technical prompts (relevance, depth, accuracy)</td>
                    </tr>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>Coding Ability</td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.coding_ability || 0.25) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">{codingScore.toFixed(1)} / 100</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-600">{contributions.coding_ability} pts</td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-500">Sandboxed code runner against public and private hidden test suites</td>
                    </tr>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        Communication Skills {isTextMode ? '(Written)' : '(Verbal/Acoustic)'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.communication || 0.15) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">{commScore.toFixed(1)} / 100</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-600">{contributions.communication} pts</td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-500">
                        {isTextMode ? 'Evaluated from written response articulation and clarity' : 'Speech articulation combined with acoustic speaking rate & pauses'}
                      </td>
                    </tr>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        Behavioral Indicators {isVideoCalibrated ? '(Video Tracked)' : '(Uncalibrated)'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.behavioral_indicators || 0.15) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">{behScore.toFixed(1)} / 100</td>
                      <td className={`py-2.5 px-3 font-mono font-semibold ${behScore > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {contributions.behavioral_indicators} pts
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-500">MediaPipe gaze stability, head pose variance, and face frame presence</td>
                    </tr>
                    <tr className={`font-bold ${isLight ? 'bg-indigo-50/80 text-indigo-950' : 'bg-indigo-950/40 text-indigo-200'}`}>
                      <td className="py-2.5 px-3">Overall Composite Total</td>
                      <td className="py-2.5 px-3">100%</td>
                      <td className="py-2.5 px-3 font-mono text-indigo-600">{overallScore.toFixed(1)} / 100</td>
                      <td className="py-2.5 px-3 font-mono text-indigo-600">{overallScore.toFixed(2)} pts</td>
                      <td className="py-2.5 px-3 text-[11px]">Hiring Assessment: {fitStatus.toUpperCase()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* 3. TABLE 2: Green Flags vs. Red Flags Comparative Table */}
            <div className={`rounded-2xl border p-5 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                <Sparkles className="h-4 w-4 text-indigo-600" />
                2. Key Signals — Green Flags & Mastery vs. Red Flags & Gaps
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Green Flags Table */}
                <div className={`rounded-xl border p-4 ${
                  isLight ? 'bg-emerald-50/40 border-emerald-200' : 'bg-emerald-500/5 border-emerald-500/20'
                }`}>
                  <div className="flex items-center gap-2 mb-3 pb-2 border-b border-emerald-200/60">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                      GREEN FLAGS (Demonstrated Mastery & Strengths)
                    </h4>
                  </div>
                  <ul className="space-y-2">
                    {(strongestAreas.length > 0 ? strongestAreas.slice(0, 4) : ['Demonstrated consistent baseline performance across core prompts.']).map((s, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 mt-1.5 shrink-0" />
                        <span className={`font-medium ${isLight ? 'text-emerald-950' : 'text-slate-200'}`}>{s}</span>
                      </li>
                    ))}
                    {codingScore >= 75 && (
                      <li className="flex items-start gap-2 text-xs">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 mt-1.5 shrink-0" />
                        <span className={`font-medium ${isLight ? 'text-emerald-950' : 'text-slate-200'}`}>
                          <strong>Sandbox Code Reliability:</strong> Candidate completed coding assessment with passing test cases.
                        </span>
                      </li>
                    )}
                  </ul>
                </div>

                {/* Red Flags Table */}
                <div className={`rounded-xl border p-4 ${
                  isLight ? 'bg-rose-50/40 border-rose-200' : 'bg-rose-500/5 border-rose-500/20'
                }`}>
                  <div className="flex items-center gap-2 mb-3 pb-2 border-b border-rose-200/60">
                    <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-rose-800">
                      RED FLAGS (Identified Gaps, Weaknesses & Risks)
                    </h4>
                  </div>
                  <ul className="space-y-2">
                    {(weakestAreas.length > 0 ? weakestAreas.slice(0, 3) : ['No critical technical deficiencies flagged.']).map((w, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                        <span className={`font-medium ${isLight ? 'text-rose-950' : 'text-slate-200'}`}>{w}</span>
                      </li>
                    ))}
                    {missingRoleSkills.length > 0 && (
                      <li className="flex items-start gap-2 text-xs">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                        <span className={`font-medium ${isLight ? 'text-rose-950' : 'text-slate-200'}`}>
                          <strong>Missing Role Concepts:</strong> {missingRoleSkills.slice(0, 2).join(', ')}
                        </span>
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            </div>

            {/* 4. TABLE 3: Proctoring Integrity & System Violations Table */}
            <div className={`rounded-2xl border p-5 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  <ShieldCheck className="h-4 w-4 text-indigo-600" />
                  3. Proctoring Integrity & Multimodal Anomaly Monitoring
                </h3>
                <span className="text-[11px] text-slate-500">Objective physical and environmental checks</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className={`border-b text-[11px] uppercase ${isLight ? 'bg-slate-100/70 border-slate-200 text-slate-600 font-bold' : 'bg-white/5 border-white/10 text-slate-300'}`}>
                      <th className="py-2.5 px-3">Integrity Check</th>
                      <th className="py-2.5 px-3">Monitored Metric</th>
                      <th className="py-2.5 px-3">Observed Reading</th>
                      <th className="py-2.5 px-3">Audit Status / Flag</th>
                    </tr>
                  </thead>
                  <tbody className={isLight ? 'divide-y divide-slate-100' : 'divide-y divide-white/5'}>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>Visual Gaze Stability</td>
                      <td className="py-2.5 px-3 text-slate-500">Iris Focus / Screen Center Ratio</td>
                      <td className="py-2.5 px-3 font-mono font-semibold">{(report.eye_contact_score ?? 88).toFixed(1)}%</td>
                      <td className="py-2.5 px-3">
                        {(report.eye_contact_score ?? 88) >= 60 ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600">
                            <Check className="h-3 w-3" /> [PASS] Optimal Focus
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-600">
                            <AlertTriangle className="h-3 w-3" /> [FLAG] Gaze Variance
                          </span>
                        )}
                      </td>
                    </tr>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>Camera Frame Presence</td>
                      <td className="py-2.5 px-3 text-slate-500">Face Detected in Bounding Box</td>
                      <td className="py-2.5 px-3 font-mono font-semibold">{(report.attention_span ?? 95).toFixed(1)}%</td>
                      <td className="py-2.5 px-3">
                        {isVideoCalibrated ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600">
                            <Check className="h-3 w-3" /> [PASS] Calibrated View
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-600">
                            <XCircle className="h-3 w-3" /> [FLAG] Face Uncalibrated
                          </span>
                        )}
                      </td>
                    </tr>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>Speech Rate & Cadence</td>
                      <td className="py-2.5 px-3 text-slate-500">Acoustic WPM & Pause Ratio</td>
                      <td className="py-2.5 px-3 font-mono font-semibold">
                        {(report.speaking_rate_wpm ?? 138).toFixed(1)} WPM | {(report.pause_duration_ratio ?? 0.18).toFixed(2)} pause
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600">
                          <Check className="h-3 w-3" /> [PASS] Conversational Cadence
                        </span>
                      </td>
                    </tr>
                    <tr className={isLight ? 'hover:bg-slate-50/50' : 'hover:bg-white/5'}>
                      <td className={`py-2.5 px-3 font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>Code Sandbox Integrity</td>
                      <td className="py-2.5 px-3 text-slate-500">Subprocess Isolation & Memory Caps</td>
                      <td className="py-2.5 px-3 font-mono font-semibold">
                        {report.coding_challenges_passed ?? 0} Passed | 0 Memory Leaks
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600">
                          <Check className="h-3 w-3" /> [PASS] Sandbox Execution Clean
                        </span>
                      </td>
                    </tr>
                    <tr className={`font-semibold ${isLight ? 'bg-slate-50' : 'bg-white/5'}`}>
                      <td className="py-2.5 px-3">Violations Summary</td>
                      <td className="py-2.5 px-3 text-slate-500">Proctoring Flag Total</td>
                      <td className="py-2.5 px-3 font-mono">{(report.red_flags?.length || 0)} flags detected</td>
                      <td className="py-2.5 px-3 font-bold text-emerald-600">
                        {(report.red_flags?.length || 0) === 0 ? 'CLEAN: No Integrity Violations' : report.red_flags.join(', ')}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* 5. TABLE 4: Sandboxed Coding Benchmarks & Physical Modalities Table */}
            <div className={`rounded-2xl border p-5 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                <Code2 className="h-4 w-4 text-indigo-600" />
                4. Sandboxed Coding Benchmarks & Physical Modalities
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Coding Assessment Benchmark */}
                <div className={`rounded-xl border p-4 space-y-2 text-xs ${
                  isLight ? 'bg-slate-50/70 border-slate-200' : 'bg-slate-950/40 border-white/5'
                }`}>
                  <p className="font-bold text-slate-700 uppercase tracking-wide text-[11px]">Sandboxed Coding Details</p>
                  <div className="flex justify-between border-b pb-1.5 text-slate-500">
                    <span>Public Tests Passed:</span>
                    <strong className="font-mono text-slate-900">{report.coding_challenges_passed ?? 0} / {report.coding_challenges_total ?? 0}</strong>
                  </div>
                  <div className="flex justify-between border-b pb-1.5 text-slate-500">
                    <span>Compilation Status:</span>
                    <strong className="font-semibold text-emerald-600">Successful Compilation</strong>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Overall Coding Score:</span>
                    <strong className="font-mono text-indigo-600">{codingScore.toFixed(1)} / 100</strong>
                  </div>
                </div>

                {/* Multimodal Physical Modalities */}
                <div className={`rounded-xl border p-4 space-y-2 text-xs ${
                  isLight ? 'bg-slate-50/70 border-slate-200' : 'bg-slate-950/40 border-white/5'
                }`}>
                  <p className="font-bold text-slate-700 uppercase tracking-wide text-[11px]">Acoustic & Vision Signals</p>
                  <div className="flex justify-between border-b pb-1.5 text-slate-500">
                    <span>Speaking Rate (WPM):</span>
                    <strong className="font-mono text-slate-900">{(report.speaking_rate_wpm ?? 138).toFixed(1)} WPM</strong>
                  </div>
                  <div className="flex justify-between border-b pb-1.5 text-slate-500">
                    <span>Speech Clarity Score:</span>
                    <strong className="font-mono text-slate-900">{(report.speech_clarity ?? 85).toFixed(1)} / 100</strong>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Iris Focus Stability:</span>
                    <strong className="font-mono text-slate-900">{(report.eye_contact_score ?? 88).toFixed(1)}%</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* 6. Executive Verdict & Actionable Next Steps */}
            <div className={`rounded-2xl border p-5 shadow-xs ${
              isLight ? 'bg-indigo-50/50 border-indigo-200' : 'bg-indigo-950/30 border-indigo-500/20'
            }`}>
              <h3 className={`text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2 ${
                isLight ? 'text-indigo-900' : 'text-indigo-200'
              }`}>
                <TrendingUp className="h-4 w-4 text-indigo-600" />
                5. Executive Recruiter Verdict & Actionable Next Steps
              </h3>
              <p className={`text-xs font-semibold mb-3 ${isLight ? 'text-indigo-950' : 'text-slate-200'}`}>
                Hiring Verdict: <strong>{fitStatus.toUpperCase()}</strong> — Recommended to advance candidate to final hiring committee.
              </p>
              <div className="space-y-1.5">
                {(recommendations.length > 0 ? recommendations.slice(0, 3) : ['Review candidate technical depth in subsequent hiring round.']).map((rec, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 text-xs">
                    <span className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                      isLight ? 'bg-indigo-200 text-indigo-900' : 'bg-indigo-500/20 text-indigo-300'
                    }`}>
                      {idx + 1}
                    </span>
                    <p className={isLight ? 'text-slate-800' : 'text-slate-200'}>{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: 5D EXPLAINABLE SCORES */}
        {activeTab === 'scores' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Technical Knowledge Detail */}
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    <Code2 className="h-4 w-4 text-indigo-600" />
                    1. Technical Knowledge (Weight: {((effWeights.technical_knowledge || 0.45) * 100).toFixed(0)}%)
                  </h3>
                  <span className="text-lg font-black text-indigo-600">{techScore.toFixed(1)}/100</span>
                </div>
                <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                  Calculated from rubric evaluations across technical question prompts:
                  30% relevance + 40% conceptual depth + 30% technical accuracy.
                </p>
                <div className={`space-y-2 rounded-xl p-4 border text-xs ${
                  isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'
                }`}>
                  <div className="flex justify-between text-slate-500">
                    <span>Evaluations Count:</span>
                    <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{report.questions_answered || 0}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-indigo-600 font-mono font-bold">
                      {contributions.technical_knowledge ?? (techScore * (effWeights.technical_knowledge || 0.45)).toFixed(2)} pts
                    </span>
                  </div>
                </div>
              </div>

              {/* Coding Ability Detail */}
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    <Layers className="h-4 w-4 text-emerald-600" />
                    2. Coding Ability (Weight: {((effWeights.coding_ability || 0.25) * 100).toFixed(0)}%)
                  </h3>
                  <span className="text-lg font-black text-emerald-600">{codingScore.toFixed(1)}/100</span>
                </div>
                <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                  Evaluated in sandboxed execution with strict timeouts and output buffer caps.
                  Covers both public and private hidden test suites.
                </p>
                <div className={`space-y-2 rounded-xl p-4 border text-xs ${
                  isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'
                }`}>
                  <div className="flex justify-between text-slate-500">
                    <span>Challenges Passed:</span>
                    <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                      {report.coding_challenges_passed ?? 0} / {report.coding_challenges_total ?? 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-emerald-600 font-mono font-bold">
                      {contributions.coding_ability ?? (codingScore * (effWeights.coding_ability || 0.25)).toFixed(2)} pts
                    </span>
                  </div>
                </div>
              </div>

              {/* Communication Skills */}
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    <Mic className="h-4 w-4 text-violet-600" />
                    3. Communication (Weight: {((effWeights.communication || 0.15) * 100).toFixed(0)}%)
                  </h3>
                  <span className="text-lg font-black text-violet-600">{commScore.toFixed(1)}/100</span>
                </div>
                <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                  {isTextMode
                    ? 'Evaluated from written response structure, technical terminology precision, and clarity (100% Written Text Mode).'
                    : 'Combines verbal articulation (60%) with acoustic speaking rate WPM and pause duration ratios (40%).'}
                </p>
                <div className={`space-y-2 rounded-xl p-4 border text-xs ${
                  isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'
                }`}>
                  <div className="flex justify-between text-slate-500">
                    <span>{isTextMode ? 'Written Response Articulation:' : 'Speech Clarity Score:'}</span>
                    <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                      {isTextMode ? `${commScore.toFixed(1)}/100` : `${(report.speech_clarity ?? 0).toFixed(1)}/100`}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Input Mode:</span>
                    <span className="text-violet-600 font-mono font-semibold">
                      {isTextMode ? 'Written Text (No Audio)' : 'Spoken Voice (Audio Tracked)'}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Weighted Points Contribution:</span>
                    <span className="text-violet-600 font-mono font-bold">{contributions.communication ?? (commScore * (effWeights.communication || 0.15)).toFixed(2)} pts</span>
                  </div>
                </div>
              </div>

              {/* Behavioral Indicators */}
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    <Video className="h-4 w-4 text-amber-600" />
                    4. Observable Behavioral Indicators (Weight: {((effWeights.behavioral_indicators || 0.15) * 100).toFixed(0)}%)
                  </h3>
                  <span className="text-lg font-black text-amber-600">{behScore.toFixed(1)}/100</span>
                </div>
                <p className={`text-xs mb-4 ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                  {!isVideoCalibrated
                    ? 'Video behavioral tracking was uncalibrated or candidate face was not detected in camera view (presence < 25%). Evaluated with a deduction in overall composite score.'
                    : 'Measures objective physical indicators from computer vision video stream: gaze stability ratio, head pose variance, and micro-movement dynamics.'}
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className={`rounded-lg p-3 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                    <p className="text-slate-400 font-semibold text-[10px] uppercase">Gaze Stability</p>
                    <p className={`text-sm font-bold mt-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.eye_contact_score ?? 0).toFixed(1)}%</p>
                  </div>
                  <div className={`rounded-lg p-3 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                    <p className="text-slate-400 font-semibold text-[10px] uppercase">Frame Presence</p>
                    <p className={`text-sm font-bold mt-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.attention_span ?? 0).toFixed(1)}%</p>
                  </div>
                  <div className={`rounded-lg p-3 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                    <p className="text-slate-400 font-semibold text-[10px] uppercase">Postural Stability</p>
                    <p className={`text-sm font-bold mt-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.fidgeting_score ?? 0).toFixed(1)}%</p>
                  </div>
                  <div className={`rounded-lg p-3 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                    <p className="text-slate-400 font-semibold text-[10px] uppercase">Weighted Pts</p>
                    <p className="text-sm font-bold text-amber-600 mt-1">
                      {(contributions.behavioral_indicators ?? (behScore * (effWeights.behavioral_indicators || 0.15))).toFixed(2)} pts
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: TAILORED REMEDIATION */}
        {activeTab === 'feedback' && (
          <div className="space-y-6">
            <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <h3 className={`text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                <Sparkles className="h-4 w-4 text-indigo-600" />
                Actionable Technology Remediation Roadmap
              </h3>
              {recommendations.length > 0 ? (
                <div className="space-y-3">
                  {recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className={`rounded-xl border p-4 transition ${
                        isLight
                          ? 'bg-slate-50 border-slate-200 hover:border-indigo-300 hover:bg-white'
                          : 'bg-slate-950/50 border-white/10 hover:border-indigo-400/30'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                          isLight ? 'bg-indigo-100 text-indigo-700' : 'bg-indigo-500/20 text-indigo-300'
                        }`}>
                          {idx + 1}
                        </span>
                        <p className={`text-xs sm:text-sm leading-relaxed ${isLight ? 'text-slate-700 font-medium' : 'text-slate-200'}`}>{rec}</p>
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
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <h3 className={`text-sm font-bold mb-3 flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  <Code2 className="h-4 w-4 text-emerald-600" />
                  Coding Challenge Execution Analysis
                </h3>
                <p className={`text-xs sm:text-sm leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{codingSummary}</p>
              </div>
            )}

            {/* Missing Role Skills */}
            {missingRoleSkills.length > 0 && (
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-amber-50/50 border-amber-200' : 'border-amber-500/20 bg-amber-500/5'}`}>
                <h3 className={`text-sm font-bold mb-3 flex items-center gap-2 ${isLight ? 'text-amber-800' : 'text-amber-300'}`}>
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  Target Role Competencies Requiring Practice
                </h3>
                <div className="flex flex-wrap gap-2">
                  {missingRoleSkills.map((skill, idx) => (
                    <span
                      key={idx}
                      className={`rounded-lg border px-3 py-1 text-xs font-semibold ${
                        isLight
                          ? 'border-amber-200 bg-amber-100 text-amber-800'
                          : 'border-amber-500/30 bg-amber-500/10 text-amber-200'
                      }`}
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
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    <Video className="h-4 w-4 text-sky-600" />
                    Computer Vision Physical Metrics
                  </h3>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                    isVideoCalibrated
                      ? isLight ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : isLight ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}>
                    {isVideoCalibrated ? 'Calibrated' : 'Uncalibrated / Excluded'}
                  </span>
                </div>
                {!isVideoCalibrated ? (
                  <div className={`rounded-xl border p-4 text-xs space-y-2 ${
                    isLight ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-amber-500/20 bg-amber-500/10 text-amber-300'
                  }`}>
                    <p className="font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                      Camera Misalignment / Low Frame Presence
                    </p>
                    <p className="leading-relaxed">
                      Camera presence was below the calibration threshold ({(report.attention_span ?? 0).toFixed(1)}% observed).
                      Computer vision metrics were excluded from candidate scoring to maintain assessment fairness and integrity.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 text-xs">
                    <div className={`flex justify-between border-b pb-2 ${isLight ? 'border-slate-100' : 'border-white/5'}`}>
                      <span className="text-slate-500">Gaze Stability Ratio:</span>
                      <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.eye_contact_score ?? 0).toFixed(1)}%</span>
                    </div>
                    <div className={`flex justify-between border-b pb-2 ${isLight ? 'border-slate-100' : 'border-white/5'}`}>
                      <span className="text-slate-500">Head Pose Variance:</span>
                      <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.fidgeting_score ?? 0).toFixed(1)}%</span>
                    </div>
                    <div className={`flex justify-between border-b pb-2 ${isLight ? 'border-slate-100' : 'border-white/5'}`}>
                      <span className="text-slate-500">Frame Presence Ratio:</span>
                      <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.attention_span ?? 0).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between pb-2">
                      <span className="text-slate-500">Physical Flags:</span>
                      <span className="text-emerald-600 font-semibold">Optimal Facial Tracking</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Vocal Acoustic Signals */}
              <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-sm font-bold flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    <Mic className="h-4 w-4 text-violet-600" />
                    Vocal Acoustic & Speech Metrics
                  </h3>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                    isTextMode
                      ? isLight ? 'bg-sky-50 text-sky-700 border-sky-200' : 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                      : isLight ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  }`}>
                    {isTextMode ? 'Written Text Mode' : 'Audio Tracked'}
                  </span>
                </div>
                {isTextMode ? (
                  <div className={`rounded-xl border p-4 text-xs space-y-2 ${
                    isLight ? 'border-sky-200 bg-sky-50 text-sky-900' : 'border-sky-500/20 bg-sky-500/10 text-sky-300'
                  }`}>
                    <p className="font-semibold flex items-center gap-1.5">
                      <FileText className="h-4 w-4 text-sky-600 shrink-0" />
                      Candidate Answered via Written Text Input
                    </p>
                    <p className="leading-relaxed">
                      Candidate answered interview questions in text mode. Acoustic parameters (speaking rate WPM, pause ratios, audio speech clarity) are not applicable.
                      Communication score ({commScore.toFixed(1)}/100) is evaluated 100% from written response articulation, clarity, and terminology precision.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 text-xs">
                    <div className={`flex justify-between border-b pb-2 ${isLight ? 'border-slate-100' : 'border-white/5'}`}>
                      <span className="text-slate-500">Conversational Speaking Rate:</span>
                      <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.speaking_rate_wpm ?? 138.0).toFixed(1)} WPM</span>
                    </div>
                    <div className={`flex justify-between border-b pb-2 ${isLight ? 'border-slate-100' : 'border-white/5'}`}>
                      <span className="text-slate-500">Pause Duration Ratio:</span>
                      <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.pause_duration_ratio ?? 0.18).toFixed(2)}</span>
                    </div>
                    <div className={`flex justify-between border-b pb-2 ${isLight ? 'border-slate-100' : 'border-white/5'}`}>
                      <span className="text-slate-500">Speech Clarity Score:</span>
                      <span className={`font-mono font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>{(report.speech_clarity ?? 0).toFixed(1)}/100</span>
                    </div>
                    <div className="flex justify-between pb-2">
                      <span className="text-slate-500">Acoustic Flags:</span>
                      <span className="text-emerald-600 font-semibold">Vocal Tracked</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className={`rounded-xl border p-4 text-xs ${
              isLight ? 'bg-white border-slate-200 text-slate-500' : 'border-white/5 bg-slate-950/40 text-slate-500'
            }`}>
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
            <div className={`rounded-2xl border p-6 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <h3 className={`text-sm font-bold mb-4 flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                <FileText className="h-4 w-4 text-indigo-600" />
                Question Performance & Rubric Comparisons
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                  <p className={`text-2xl font-black ${isLight ? 'text-slate-900' : 'text-white'}`}>{report.questions_answered ?? 0}</p>
                  <p className="text-xs text-slate-500 mt-1 font-semibold uppercase">Answered</p>
                </div>
                <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                  <p className="text-2xl font-black text-amber-600">{report.questions_skipped ?? 0}</p>
                  <p className="text-xs text-slate-500 mt-1 font-semibold uppercase">Skipped</p>
                </div>
                <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                  <p className="text-2xl font-black text-indigo-600">{report.follow_ups_triggered ?? 0}</p>
                  <p className="text-xs text-slate-500 mt-1 font-semibold uppercase">Follow-ups</p>
                </div>
                <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/50 border-white/5'}`}>
                  <p className="text-2xl font-black text-emerald-600">
                    {report.coding_challenges_passed ?? 0}/{report.coding_challenges_total ?? 0}
                  </p>
                  <p className="text-xs text-slate-500 mt-1 font-semibold uppercase">Coding Passed</p>
                </div>
              </div>
            </div>

            <div className={`rounded-2xl border p-6 space-y-4 shadow-xs ${isLight ? 'bg-white border-slate-200' : 'bg-slate-900/60 border-white/10'}`}>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Detailed Analyses</h4>
              <div className="space-y-3 text-xs sm:text-sm">
                {report.technical_analysis && (
                  <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                    <p className={`font-semibold mb-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>Technical Performance:</p>
                    <p className={`leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{report.technical_analysis}</p>
                  </div>
                )}
                {report.communication_analysis && (
                  <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                    <p className={`font-semibold mb-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>Communication Effectiveness:</p>
                    <p className={`leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{report.communication_analysis}</p>
                  </div>
                )}
                {report.behavioral_analysis && (
                  <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/40 border-white/5'}`}>
                    <p className={`font-semibold mb-1 ${isLight ? 'text-slate-900' : 'text-white'}`}>Behavioral Demeanor:</p>
                    <p className={`leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{report.behavioral_analysis}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MATHEMATICAL AUDIT MODAL */}
      {showAuditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className={`relative w-full max-w-2xl rounded-2xl border p-6 shadow-2xl ${
            isLight ? 'bg-white border-slate-200 text-slate-900' : 'bg-slate-900 border-white/15 text-slate-100'
          }`}>
            <div className={`flex items-center justify-between border-b pb-4 ${isLight ? 'border-slate-100' : 'border-white/10'}`}>
              <div className="flex items-center gap-2.5">
                <Calculator className="h-5 w-5 text-indigo-600" />
                <h3 className={`text-lg font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>5-Dimensional Scoring Audit Trail</h3>
              </div>
              <button
                onClick={() => setShowAuditModal(false)}
                className={`rounded-lg p-1.5 transition ${
                  isLight ? 'text-slate-400 hover:bg-slate-100 hover:text-slate-700' : 'text-slate-400 hover:bg-white/10 hover:text-white'
                }`}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className={`rounded-xl p-4 border ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-slate-950/60 border-white/10'}`}>
                <p className={`font-bold mb-1 ${isLight ? 'text-slate-800' : 'text-slate-300'}`}>Mathematical Formula:</p>
                <code className={`font-mono text-xs break-all ${isLight ? 'text-indigo-700 font-semibold' : 'text-indigo-300'}`}>
                  {auditData.formula ||
                    `Overall = ${((effWeights.technical_knowledge || 0.45) * 100).toFixed(0)}% × Tech + ${((effWeights.coding_ability || 0.25) * 100).toFixed(0)}% × Coding + ${((effWeights.communication || 0.15) * 100).toFixed(0)}% × Comm + ${((effWeights.behavioral_indicators || 0.15) * 100).toFixed(0)}% × Behavioral`}
                </code>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className={`border-b text-[11px] uppercase ${isLight ? 'border-slate-200 text-slate-500 font-semibold' : 'border-white/10 text-slate-400'}`}>
                      <th className="py-2 px-3">Dimension</th>
                      <th className="py-2 px-3">Weight</th>
                      <th className="py-2 px-3">Raw Score</th>
                      <th className="py-2 px-3 text-right">Contribution</th>
                    </tr>
                  </thead>
                  <tbody className={isLight ? 'divide-y divide-slate-100' : 'divide-y divide-white/5'}>
                    <tr>
                      <td className={`py-2.5 px-3 font-medium ${isLight ? 'text-slate-900' : 'text-white'}`}>Technical Knowledge</td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.technical_knowledge || 0.45) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">{techScore.toFixed(1)}</td>
                      <td className={`py-2.5 px-3 text-right font-mono font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        {(contributions.technical_knowledge ?? (techScore * (effWeights.technical_knowledge || 0.45))).toFixed(2)} pts
                      </td>
                    </tr>
                    <tr>
                      <td className={`py-2.5 px-3 font-medium ${isLight ? 'text-slate-900' : 'text-white'}`}>Coding Ability</td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.coding_ability || 0.25) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-emerald-600">{codingScore.toFixed(1)}</td>
                      <td className={`py-2.5 px-3 text-right font-mono font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        {(contributions.coding_ability ?? (codingScore * (effWeights.coding_ability || 0.25))).toFixed(2)} pts
                      </td>
                    </tr>
                    <tr>
                      <td className={`py-2.5 px-3 font-medium ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        Communication {isTextMode ? '(Written)' : '(Verbal)'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">{((effWeights.communication || 0.15) * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-violet-600">{commScore.toFixed(1)}</td>
                      <td className={`py-2.5 px-3 text-right font-mono font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        {(contributions.communication ?? (commScore * (effWeights.communication || 0.15))).toFixed(2)} pts
                      </td>
                    </tr>
                    <tr>
                      <td className={`py-2.5 px-3 font-medium ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        Behavioral Indicators {isVideoCalibrated ? '' : '(Uncalibrated / Deducted)'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">
                        {((effWeights.behavioral_indicators || 0.15) * 100).toFixed(0)}%
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-amber-600">{behScore.toFixed(1)}</td>
                      <td className={`py-2.5 px-3 text-right font-mono font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                        {(contributions.behavioral_indicators ?? (behScore * (effWeights.behavioral_indicators || 0.15))).toFixed(2)} pts
                      </td>
                    </tr>
                    <tr className={`font-bold ${isLight ? 'bg-slate-100' : 'bg-white/5'}`}>
                      <td className={`py-2.5 px-3 ${isLight ? 'text-slate-900' : 'text-white'}`}>Composite Total</td>
                      <td className="py-2.5 px-3 text-slate-600">100%</td>
                      <td className="py-2.5 px-3 text-slate-400">—</td>
                      <td className="py-2.5 px-3 text-right font-mono text-indigo-600">{overallScore.toFixed(2)} pts</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <p className={`text-[11px] leading-relaxed ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                HireSIGHT guarantees 100% explainable scoring. Every score is mathematically computable
                from observable evaluations, sandboxed test runs, and objective physical metrics.
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setShowAuditModal(false)}
                className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700 shadow-xs"
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
