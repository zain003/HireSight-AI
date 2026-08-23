/**
 * Recruiter Report Viewer Component
 * Displays comprehensive hiring decision report for HR/Recruiters
 */
import { useState } from 'react';

export default function RecruiterReportViewer({ report, sessionId }) {
  const [activeTab, setActiveTab] = useState('summary');

  if (!report) {
    return (
      <div className="min-h-screen bg-[#0B1120] text-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-slate-900/50 rounded-lg p-8 text-center">
            <p className="text-slate-400">No report available</p>
          </div>
        </div>
      </div>
    );
  }

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'Strong Hire':
        return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'Hire':
        return 'bg-green-500/10 text-green-400 border-green-500/20';
      case 'Maybe':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'No Hire':
        return 'bg-red-500/20 text-red-300 border-red-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  const ScoreCircle = ({ score, label, size = 'large' }) => {
    const getColor = (s) => {
      if (s >= 80) return 'text-green-400';
      if (s >= 60) return 'text-yellow-400';
      return 'text-red-400';
    };

    const radius = size === 'large' ? 45 : 35;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    return (
      <div className="flex flex-col items-center">
        <div className="relative">
          <svg width={size === 'large' ? 120 : 90} height={size === 'large' ? 120 : 90}>
            <circle
              cx={size === 'large' ? 60 : 45}
              cy={size === 'large' ? 60 : 45}
              r={radius}
              stroke="currentColor"
              strokeWidth="6"
              fill="none"
              className="text-slate-800"
            />
            <circle
              cx={size === 'large' ? 60 : 45}
              cy={size === 'large' ? 60 : 45}
              r={radius}
              stroke="currentColor"
              strokeWidth="6"
              fill="none"
              className={getColor(score)}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size === 'large' ? 60 : 45} ${size === 'large' ? 60 : 45})`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`font-bold ${size === 'large' ? 'text-3xl' : 'text-2xl'} ${getColor(score)}`}>
              {Math.round(score)}
            </span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
        </div>
        <p className="text-sm text-slate-400 mt-2">{label}</p>
      </div>
    );
  };

  const MetricBar = ({ label, value }) => {
    const getColor = (v) => {
      if (v >= 80) return 'bg-green-500';
      if (v >= 60) return 'bg-yellow-500';
      return 'bg-red-500';
    };

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-slate-300">{label}</span>
          <span className="text-slate-400">{Math.round(value)}/100</span>
        </div>
        <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${getColor(value)}`}
            style={{ width: `${Math.min(100, value)}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0B1120] text-slate-100">
      {/* Header */}
      <div className="bg-slate-900/50 border-b border-white/10">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Interview Report</h1>
              <p className="text-slate-400 mt-1">
                {report.candidate_name} • {report.job_role}
              </p>
              <p className="text-sm text-slate-500 mt-1">
                {report.interview_date} • {report.session_duration_minutes} minutes
              </p>
            </div>
            <div className={`px-4 py-2 rounded-lg border ${getRecommendationColor(report.hiring_recommendation)}`}>
              <p className="text-sm font-semibold">{report.hiring_recommendation}</p>
              <p className="text-xs opacity-75">Confidence: {report.confidence_level}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-slate-900/30 border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex gap-6">
            {['summary', 'scores', 'analysis', 'details'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-medium capitalize transition-colors border-b-2 ${
                  activeTab === tab
                    ? 'border-indigo-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {/* Overall Score */}
            <div className="bg-slate-900/50 rounded-lg p-8 border border-white/10">
              <div className="flex items-center justify-between">
                <ScoreCircle score={report.overall_score} label="Overall Score" />
                <div className="flex-1 ml-12 space-y-4">
                  <ScoreCircle score={report.technical_score} label="Technical" size="small" />
                  <ScoreCircle score={report.communication_score} label="Communication" size="small" />
                </div>
                <div className="flex-1 space-y-4">
                  <ScoreCircle score={report.behavioral_score} label="Behavioral" size="small" />
                  <ScoreCircle score={report.coding_score} label="Coding" size="small" />
                </div>
              </div>
            </div>

            {/* Executive Summary */}
            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Executive Summary</h3>
              <p className="text-slate-300 whitespace-pre-line leading-relaxed">
                {report.executive_summary}
              </p>
            </div>

            {/* Strengths & Red Flags */}
            <div className="grid grid-cols-2 gap-6">
              {/* Strengths */}
              <div className="bg-green-500/10 rounded-lg p-6 border border-green-500/20">
                <h3 className="text-lg font-semibold text-green-300 mb-4">
                  ✓ Strengths ({report.strengths?.length || 0})
                </h3>
                <ul className="space-y-2">
                  {report.strengths?.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-green-200">
                      <span className="text-green-400 mt-1">•</span>
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Red Flags */}
              <div className="bg-red-500/10 rounded-lg p-6 border border-red-500/20">
                <h3 className="text-lg font-semibold text-red-300 mb-4">
                  ⚠ Concerns ({report.red_flags?.length || 0})
                </h3>
                {report.red_flags && report.red_flags.length > 0 ? (
                  <ul className="space-y-2">
                    {report.red_flags.map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-red-200">
                        <span className="text-red-400 mt-1">•</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-red-200">No significant concerns detected</p>
                )}
              </div>
            </div>

            {/* Next Steps */}
            <div className="bg-blue-500/10 rounded-lg p-6 border border-blue-500/20">
              <h3 className="text-lg font-semibold text-blue-300 mb-4">Recommended Next Steps</h3>
              <pre className="text-sm text-blue-200 whitespace-pre-line font-sans">
                {report.next_steps}
              </pre>
            </div>
          </div>
        )}

        {/* Scores Tab */}
        {activeTab === 'scores' && (
          <div className="space-y-6">
            {/* Category Scores */}
            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-6">Category Scores</h3>
              <div className="space-y-4">
                <MetricBar label="Technical Knowledge" value={report.technical_score} />
                <MetricBar label="Communication Skills" value={report.communication_score} />
                <MetricBar label="Behavioral/Professional" value={report.behavioral_score} />
                <MetricBar label="Coding Ability" value={report.coding_score} />
              </div>
            </div>

            {/* Detailed Metrics */}
            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-6">Detailed Metrics</h3>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <MetricBar label="Vocal Confidence" value={report.vocal_confidence} />
                  <MetricBar label="Speech Clarity" value={report.speech_clarity} />
                  <MetricBar label="Eye Contact" value={report.eye_contact_score} />
                </div>
                <div className="space-y-4">
                  <MetricBar label="Attention Span" value={report.attention_span} />
                  <MetricBar label="Minimal Fidgeting" value={report.fidgeting_score} />
                  <MetricBar label="Overall Score" value={report.overall_score} />
                </div>
              </div>
            </div>

            {/* Question Performance */}
            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Question Performance</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-3xl font-bold text-white">{report.questions_answered}</p>
                  <p className="text-sm text-slate-400">Questions Answered</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-3xl font-bold text-yellow-400">{report.questions_skipped}</p>
                  <p className="text-sm text-slate-400">Questions Skipped</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-3xl font-bold text-indigo-400">{report.follow_ups_triggered}</p>
                  <p className="text-sm text-slate-400">Follow-ups Triggered</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <p className="text-3xl font-bold text-green-400">
                    {report.coding_challenges_passed}/{report.coding_challenges_total}
                  </p>
                  <p className="text-sm text-slate-400">Coding Challenges</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Tab */}
        {activeTab === 'analysis' && (
          <div className="space-y-6">
            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Technical Analysis</h3>
              <p className="text-slate-300 leading-relaxed">{report.technical_analysis}</p>
            </div>

            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Behavioral Analysis</h3>
              <p className="text-slate-300 leading-relaxed">{report.behavioral_analysis}</p>
            </div>

            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Communication Analysis</h3>
              <p className="text-slate-300 leading-relaxed">{report.communication_analysis}</p>
            </div>

            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Coding Analysis</h3>
              <p className="text-slate-300 leading-relaxed">{report.coding_analysis}</p>
            </div>
          </div>
        )}

        {/* Details Tab */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Detailed Recommendation</h3>
              <pre className="text-slate-300 whitespace-pre-line leading-relaxed font-sans">
                {report.detailed_recommendation}
              </pre>
            </div>

            {report.areas_for_improvement && report.areas_for_improvement.length > 0 && (
              <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4">Areas for Improvement</h3>
                <ul className="space-y-2">
                  {report.areas_for_improvement.map((area, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-slate-300">
                      <span className="text-yellow-400 mt-1">→</span>
                      <span>{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4">Session Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-400">Session ID</p>
                  <p className="text-white font-mono">{sessionId}</p>
                </div>
                <div>
                  <p className="text-slate-400">Duration</p>
                  <p className="text-white">{report.session_duration_minutes} minutes</p>
                </div>
                <div>
                  <p className="text-slate-400">Interview Date</p>
                  <p className="text-white">{report.interview_date}</p>
                </div>
                <div>
                  <p className="text-slate-400">Job Role</p>
                  <p className="text-white">{report.job_role}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Print Button */}
      <div className="fixed bottom-6 right-6">
        <button
          onClick={() => window.print()}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Print Report
        </button>
      </div>
    </div>
  );
}
