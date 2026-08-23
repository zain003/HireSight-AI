/**
 * Real-time Metrics Dashboard Component
 * Displays behavioral and vocal metrics during interview
 */
import { useEffect, useState } from 'react';

export default function MetricsDashboard({ 
  behavioralMetrics, 
  vocalMetrics, 
  show = true 
}) {
  const [metrics, setMetrics] = useState({
    eyeContact: 0,
    confidencePosture: 0,
    attentionSpan: 0,
    fidgeting: 0,
    vocalConfidence: 0,
    speechClarity: 0,
    communicationEffectiveness: 0
  });

  useEffect(() => {
    if (behavioralMetrics || vocalMetrics) {
      setMetrics({
        eyeContact: behavioralMetrics?.eye_contact || 0,
        confidencePosture: behavioralMetrics?.confidence_posture || 0,
        attentionSpan: behavioralMetrics?.attention_span || 0,
        fidgeting: behavioralMetrics?.fidgeting || 0,
        vocalConfidence: vocalMetrics?.vocal_confidence || 0,
        speechClarity: vocalMetrics?.speech_clarity || 0,
        communicationEffectiveness: vocalMetrics?.communication_effectiveness || 0
      });
    }
  }, [behavioralMetrics, vocalMetrics]);

  if (!show) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-500/20';
    if (score >= 60) return 'bg-yellow-500/20';
    return 'bg-red-500/20';
  };

  const MetricBar = ({ label, value, max = 100 }) => {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));
    const colorClass = getScoreColor(value);
    const bgClass = getScoreBg(value);

    return (
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">{label}</span>
          <span className={`font-semibold ${colorClass}`}>
            {Math.round(value)}%
          </span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${bgClass}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  const MetricCard = ({ icon, title, value, description }) => {
    const colorClass = getScoreColor(value);

    return (
      <div className="bg-slate-900/50 rounded-lg p-4 border border-white/5">
        <div className="flex items-center gap-3">
          <div className={`text-2xl ${colorClass}`}>{icon}</div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-400 truncate">{title}</p>
            <p className={`text-2xl font-bold ${colorClass}`}>
              {Math.round(value)}
              <span className="text-sm text-slate-500">/100</span>
            </p>
            {description && (
              <p className="text-xs text-slate-500 mt-1 truncate">{description}</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse" />
        <h3 className="text-sm font-semibold text-slate-300">
          Live Performance Metrics
        </h3>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          icon="👁️"
          title="Eye Contact"
          value={metrics.eyeContact}
          description="Camera engagement"
        />
        <MetricCard
          icon="🎤"
          title="Vocal Confidence"
          value={metrics.vocalConfidence}
          description="Speech delivery"
        />
        <MetricCard
          icon="🧘"
          title="Posture"
          value={metrics.confidencePosture}
          description="Body language"
        />
        <MetricCard
          icon="💬"
          title="Clarity"
          value={metrics.speechClarity}
          description="Communication"
        />
      </div>

      {/* Detailed Bars */}
      <div className="space-y-3 bg-slate-900/30 rounded-lg p-4 border border-white/5">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
          Detailed Analysis
        </h4>
        <MetricBar label="Eye Contact" value={metrics.eyeContact} />
        <MetricBar label="Attention Span" value={metrics.attentionSpan} />
        <MetricBar label="Confidence Posture" value={metrics.confidencePosture} />
        <MetricBar label="Minimal Fidgeting" value={metrics.fidgeting} />
        <MetricBar label="Vocal Confidence" value={metrics.vocalConfidence} />
        <MetricBar label="Speech Clarity" value={metrics.speechClarity} />
        <MetricBar 
          label="Overall Communication" 
          value={metrics.communicationEffectiveness} 
        />
      </div>

      {/* Tips */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
        <div className="flex gap-2">
          <span className="text-blue-400 text-lg">💡</span>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-blue-300 font-medium">Performance Tip</p>
            <p className="text-xs text-blue-200/70 mt-1">
              {metrics.eyeContact < 60 && "Maintain eye contact with the camera. "}
              {metrics.vocalConfidence < 60 && "Speak clearly and confidently. "}
              {metrics.fidgeting < 60 && "Keep your posture steady. "}
              {metrics.eyeContact >= 60 && metrics.vocalConfidence >= 60 && 
               metrics.fidgeting >= 60 && "Great job! Keep up the excellent performance."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
