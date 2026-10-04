/**
 * Job Candidates List Component
 * Shows all candidates who applied and completed interviews for a specific job.
 * Polished with executive White & Professional theme and Dark mode support.
 */
import { useState, useEffect } from 'react';
import api from '@/services/api';
import { Users, CheckCircle2, Clock, Award, Sparkles, AlertCircle, UserX, FileText } from 'lucide-react';

export default function JobCandidatesList({ jobPostId, onViewReport, theme = 'light' }) {
  const isLight = theme === 'light';
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('score'); // 'score', 'date', 'name'
  const [filterStatus, setFilterStatus] = useState('all'); // 'all', 'completed', 'in_progress'

  useEffect(() => {
    if (jobPostId) {
      fetchCandidates();
    }
  }, [jobPostId]);

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/auth/admin/job-posts/${jobPostId}/candidates`
      );
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch candidates');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationBadge = (recommendation) => {
    if (!recommendation) return null;
    const rec = recommendation.trim();
    if (rec === 'Strong Hire' || rec === 'Strong Fit') {
      return isLight
        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
        : 'bg-green-500/20 text-green-300 border-green-500/30';
    }
    if (rec === 'Hire' || rec === 'Potential Fit') {
      return isLight
        ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
        : 'bg-green-500/10 text-green-400 border-green-500/20';
    }
    if (rec === 'Maybe' || rec === 'Needs Growth') {
      return isLight
        ? 'bg-amber-50 text-amber-700 border-amber-200'
        : 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
    }
    return isLight
      ? 'bg-rose-50 text-rose-700 border-rose-200'
      : 'bg-red-500/20 text-red-300 border-red-500/30';
  };

  const getScoreColor = (score) => {
    if (score == null) return isLight ? 'text-slate-400' : 'text-slate-500';
    if (score >= 80) return isLight ? 'text-emerald-700' : 'text-emerald-400';
    if (score >= 60) return isLight ? 'text-amber-700' : 'text-amber-400';
    return isLight ? 'text-rose-700' : 'text-red-400';
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'completed') {
      return isLight
        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
        : 'bg-green-500/20 text-green-300 border border-green-500/30';
    }
    if (s === 'in_progress') {
      return isLight
        ? 'bg-sky-50 text-sky-700 border border-sky-200'
        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30';
    }
    if (s === 'abandoned') {
      return isLight
        ? 'bg-amber-50 text-amber-700 border border-amber-200'
        : 'bg-red-500/20 text-red-300 border border-red-500/30';
    }
    return isLight
      ? 'bg-slate-100 text-slate-600 border border-slate-200'
      : 'bg-slate-800 text-slate-400 border border-slate-700';
  };

  const getSortedAndFilteredCandidates = () => {
    if (!data?.candidates) return [];
    
    let filtered = [...data.candidates];
    
    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(c => (c.status || '').toLowerCase() === filterStatus.toLowerCase());
    }
    
    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return (b.overall_score || 0) - (a.overall_score || 0);
        case 'date':
          return new Date(b.ended_at || b.started_at) - new Date(a.ended_at || a.started_at);
        case 'name':
          return (a.candidate_name || '').localeCompare(b.candidate_name || '');
        default:
          return 0;
      }
    });
    
    return filtered;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
        <p className={`text-sm font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>Loading candidates…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`rounded-xl border p-6 text-center ${
        isLight ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-red-500/20 bg-red-500/10 text-red-300'
      }`}>
        <p className="font-semibold">Error: {error}</p>
        <button
          onClick={fetchCandidates}
          className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-xl text-white text-xs font-semibold shadow-xs transition"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const candidates = getSortedAndFilteredCandidates();

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className={`rounded-2xl p-5 border transition-all ${
          isLight ? 'bg-white border-slate-200 shadow-xs' : 'bg-slate-900/50 border-white/10'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Applicants</span>
            <Users className="h-4 w-4 text-indigo-500" />
          </div>
          <p className={`text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
            {data.total_candidates}
          </p>
        </div>

        <div className={`rounded-2xl p-5 border transition-all ${
          isLight ? 'bg-white border-emerald-200 shadow-xs' : 'bg-slate-900/50 border-white/10'
        }`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-semibold uppercase tracking-wider ${isLight ? 'text-emerald-700' : 'text-emerald-300'}`}>
              Completed
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <p className={`text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 ${isLight ? 'text-emerald-700' : 'text-emerald-400'}`}>
            {data.completed_interviews}
          </p>
        </div>

        <div className={`rounded-2xl p-5 border transition-all ${
          isLight ? 'bg-white border-sky-200 shadow-xs' : 'bg-slate-900/50 border-white/10'
        }`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-semibold uppercase tracking-wider ${isLight ? 'text-sky-700' : 'text-sky-300'}`}>
              In Progress
            </span>
            <Clock className="h-4 w-4 text-sky-500" />
          </div>
          <p className={`text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 ${isLight ? 'text-sky-700' : 'text-sky-400'}`}>
            {data.total_candidates - data.completed_interviews}
          </p>
        </div>

        <div className={`rounded-2xl p-5 border transition-all ${
          isLight ? 'bg-white border-slate-200 shadow-xs' : 'bg-slate-900/50 border-white/10'
        }`}>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Job Role</span>
          <p className={`text-base font-bold truncate mt-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
            {data.job_title}
          </p>
        </div>
      </div>

      {/* Filters and Sort */}
      <div className={`flex flex-wrap gap-4 items-center justify-between rounded-2xl p-4 border shadow-xs ${
        isLight ? 'bg-white border-slate-200' : 'bg-slate-900/30 border-white/10'
      }`}>
        <div className="flex flex-wrap gap-2 items-center">
          <span className={`text-xs font-semibold uppercase tracking-wider mr-1 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
            Filter:
          </span>
          {['all', 'completed', 'in_progress'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterStatus === status
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : isLight
                  ? 'bg-slate-100 text-slate-700 hover:bg-slate-200/70'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {status === 'all' ? 'All' : status === 'completed' ? 'Completed' : 'In Progress'}
            </button>
          ))}
        </div>
        
        <div className="flex gap-2 items-center">
          <span className={`text-xs font-medium ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition focus:outline-none ${
              isLight
                ? 'border-slate-200 bg-slate-50 text-slate-800 focus:bg-white focus:border-indigo-600'
                : 'border-white/10 bg-slate-800 text-slate-200 focus:border-indigo-500'
            }`}
          >
            <option value="score">Score (High to Low)</option>
            <option value="date">Date (Recent First)</option>
            <option value="name">Name (A–Z)</option>
          </select>
        </div>
      </div>

      {/* Candidates List */}
      {candidates.length === 0 ? (
        <div className={`rounded-2xl p-12 text-center border shadow-xs ${
          isLight ? 'bg-white border-slate-200' : 'bg-slate-900/50 border-white/10'
        }`}>
          <p className="text-slate-500 text-sm">No candidates found with current filters.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((candidate) => (
            <div
              key={candidate.session_id}
              className={`rounded-2xl border p-6 transition-all ${
                isLight
                  ? 'bg-white border-slate-200 shadow-xs hover:shadow-md hover:border-slate-300'
                  : 'bg-slate-900/50 border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                {/* Candidate Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2.5 mb-3">
                    <h3 className={`text-lg font-bold truncate ${isLight ? 'text-slate-900' : 'text-white'}`}>
                      {candidate.candidate_name}
                    </h3>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getStatusBadge(candidate.status)}`}>
                      {candidate.status}
                    </span>
                    {candidate.hiring_recommendation && (
                      <span className={`px-2.5 py-0.5 rounded-lg text-xs font-semibold border ${getRecommendationBadge(candidate.hiring_recommendation)}`}>
                        {candidate.hiring_recommendation}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                    <div>
                      <p className="text-slate-400 uppercase tracking-wider font-semibold text-[10px]">Email</p>
                      <p className={`mt-0.5 font-medium truncate ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{candidate.user_email || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 uppercase tracking-wider font-semibold text-[10px]">Experience</p>
                      <p className={`mt-0.5 font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{candidate.experience_years || 0} years</p>
                    </div>
                    <div>
                      <p className="text-slate-400 uppercase tracking-wider font-semibold text-[10px]">Interview Date</p>
                      <p className={`mt-0.5 font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                        {candidate.ended_at 
                          ? new Date(candidate.ended_at).toLocaleDateString()
                          : candidate.started_at 
                            ? new Date(candidate.started_at).toLocaleDateString()
                            : 'N/A'
                        }
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 uppercase tracking-wider font-semibold text-[10px]">Resume Score</p>
                      <p className={`mt-0.5 font-medium ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>{candidate.resume_score != null ? `${Number(candidate.resume_score).toFixed(1)}/100` : 'N/A'}</p>
                    </div>
                  </div>

                  {candidate.skills && candidate.skills.length > 0 && (
                    <div className="mt-3">
                      <p className="text-[10px] uppercase font-semibold tracking-wider text-slate-400 mb-1.5">Skills:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {candidate.skills.slice(0, 10).map((skill, idx) => (
                          <span
                            key={idx}
                            className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                              isLight
                                ? 'bg-slate-100 text-slate-700 border border-slate-200/60'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {skill}
                          </span>
                        ))}
                        {candidate.skills.length > 10 && (
                          <span className="px-1.5 py-0.5 text-slate-500 text-xs">
                            +{candidate.skills.length - 10} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Score & Action */}
                <div className="flex md:flex-col items-center md:items-end justify-between md:justify-center gap-4 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100">
                  {candidate.overall_score !== null && (
                    <div className="text-left md:text-right">
                      <p className="text-[10px] uppercase font-semibold tracking-wider text-slate-400 mb-0.5">Overall Score</p>
                      <div className="flex items-baseline md:justify-end gap-1">
                        <span className={`text-3xl font-black ${getScoreColor(candidate.overall_score)}`}>
                          {Math.round(candidate.overall_score)}
                        </span>
                        <span className="text-xs text-slate-400">/100</span>
                      </div>
                    </div>
                  )}

                  {candidate.has_report && (
                    <button
                      onClick={() => onViewReport(candidate.session_id)}
                      className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition text-xs font-semibold"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      View Full Report
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
