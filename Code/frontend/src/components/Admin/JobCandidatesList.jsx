/**
 * Job Candidates List Component
 * Shows all candidates who applied and completed interviews for a specific job
 */
import { useState, useEffect } from 'react';
import api from '@/services/api';

export default function JobCandidatesList({ jobPostId, onViewReport }) {
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
    const styles = {
      'Strong Hire': 'bg-green-500/20 text-green-300 border-green-500/30',
      'Hire': 'bg-green-500/10 text-green-400 border-green-500/20',
      'Maybe': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      'No Hire': 'bg-red-500/20 text-red-300 border-red-500/30',
    };
    return styles[recommendation] || 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  };

  const getScoreColor = (score) => {
    if (!score) return 'text-slate-500';
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStatusBadge = (status) => {
    const styles = {
      'completed': 'bg-green-500/20 text-green-300',
      'in_progress': 'bg-blue-500/20 text-blue-300',
      'abandoned': 'bg-red-500/20 text-red-300',
    };
    return styles[status] || 'bg-slate-500/20 text-slate-300';
  };

  const getSortedAndFilteredCandidates = () => {
    if (!data?.candidates) return [];
    
    let filtered = [...data.candidates];
    
    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(c => c.status === filterStatus);
    }
    
    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return (b.overall_score || 0) - (a.overall_score || 0);
        case 'date':
          return new Date(b.ended_at || b.started_at) - new Date(a.ended_at || a.started_at);
        case 'name':
          return a.candidate_name.localeCompare(b.candidate_name);
        default:
          return 0;
      }
    });
    
    return filtered;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 text-center">
        <p className="text-red-300">Error: {error}</p>
        <button
          onClick={fetchCandidates}
          className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-300 transition-colors"
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
          <p className="text-slate-400 text-sm">Total Applicants</p>
          <p className="text-3xl font-bold text-white mt-2">{data.total_candidates}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
          <p className="text-slate-400 text-sm">Completed</p>
          <p className="text-3xl font-bold text-green-400 mt-2">{data.completed_interviews}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
          <p className="text-slate-400 text-sm">In Progress</p>
          <p className="text-3xl font-bold text-blue-400 mt-2">
            {data.total_candidates - data.completed_interviews}
          </p>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-6 border border-white/10">
          <p className="text-slate-400 text-sm">Job Role</p>
          <p className="text-lg font-semibold text-white mt-2 truncate">{data.job_title}</p>
        </div>
      </div>

      {/* Filters and Sort */}
      <div className="flex flex-wrap gap-4 items-center justify-between bg-slate-900/30 rounded-lg p-4 border border-white/5">
        <div className="flex gap-2">
          <span className="text-sm text-slate-400">Filter:</span>
          {['all', 'completed', 'in_progress'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                filterStatus === status
                  ? 'bg-indigo-500 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {status === 'all' ? 'All' : status.replace('_', ' ')}
            </button>
          ))}
        </div>
        
        <div className="flex gap-2 items-center">
          <span className="text-sm text-slate-400">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-slate-800 text-slate-300 px-3 py-1 rounded-lg text-sm border border-white/10 focus:outline-none focus:border-indigo-500"
          >
            <option value="score">Score (High to Low)</option>
            <option value="date">Date (Recent First)</option>
            <option value="name">Name (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Candidates List */}
      {candidates.length === 0 ? (
        <div className="bg-slate-900/50 rounded-lg p-12 text-center border border-white/10">
          <p className="text-slate-400">No candidates found with current filters</p>
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((candidate) => (
            <div
              key={candidate.session_id}
              className="bg-slate-900/50 rounded-lg border border-white/10 hover:border-white/20 transition-colors"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  {/* Candidate Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-semibold text-white truncate">
                        {candidate.candidate_name}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs ${getStatusBadge(candidate.status)}`}>
                        {candidate.status}
                      </span>
                      {candidate.hiring_recommendation && (
                        <span className={`px-3 py-1 rounded-lg text-xs border ${getRecommendationBadge(candidate.hiring_recommendation)}`}>
                          {candidate.hiring_recommendation}
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-slate-500">Email</p>
                        <p className="text-slate-300 truncate">{candidate.user_email || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Experience</p>
                        <p className="text-slate-300">{candidate.experience_years || 0} years</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Interview Date</p>
                        <p className="text-slate-300">
                          {candidate.ended_at 
                            ? new Date(candidate.ended_at).toLocaleDateString()
                            : candidate.started_at 
                              ? new Date(candidate.started_at).toLocaleDateString()
                              : 'N/A'
                          }
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500">Resume Score</p>
                        <p className="text-slate-300">{candidate.resume_score?.toFixed(1) || 'N/A'}/100</p>
                      </div>
                    </div>

                    {candidate.skills && candidate.skills.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs text-slate-500 mb-2">Skills:</p>
                        <div className="flex flex-wrap gap-2">
                          {candidate.skills.slice(0, 10).map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs"
                            >
                              {skill}
                            </span>
                          ))}
                          {candidate.skills.length > 10 && (
                            <span className="px-2 py-1 text-slate-500 text-xs">
                              +{candidate.skills.length - 10} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Score & Action */}
                  <div className="flex flex-col items-end gap-4 ml-6">
                    {candidate.overall_score !== null && (
                      <div className="text-center">
                        <p className="text-xs text-slate-500 mb-1">Overall Score</p>
                        <p className={`text-4xl font-bold ${getScoreColor(candidate.overall_score)}`}>
                          {Math.round(candidate.overall_score)}
                        </p>
                        <p className="text-xs text-slate-500">/100</p>
                      </div>
                    )}

                    {candidate.has_report && (
                      <button
                        onClick={() => onViewReport(candidate.session_id)}
                        className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm font-medium"
                      >
                        View Full Report
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
