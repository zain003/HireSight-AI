/**
 * Admin Job Dashboard Component
 * Main dashboard for admin to view their job postings and candidate reports
 */
import { useState, useEffect } from 'react';
import JobCandidatesList from './JobCandidatesList';
import RecruiterReportViewer from '../Interview/RecruiterReportViewer';

export default function AdminJobDashboard() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('jobs'); // 'jobs', 'candidates', 'report'

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('adminToken');
      const response = await fetch('/api/admin/job-posts', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch jobs');
      }

      const data = await response.json();
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewCandidates = (job) => {
    setSelectedJob(job);
    setView('candidates');
  };

  const handleViewReport = async (sessionId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('adminToken');
      const response = await fetch(
        `/api/admin/job-posts/${selectedJob.id}/candidates/${sessionId}/report`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch report');
      }

      const data = await response.json();
      setReportData(data);
      setSelectedSession(sessionId);
      setView('report');
    } catch (error) {
      console.error('Error fetching report:', error);
      alert('Failed to load report: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (view === 'report') {
      setView('candidates');
      setReportData(null);
      setSelectedSession(null);
    } else if (view === 'candidates') {
      setView('jobs');
      setSelectedJob(null);
    }
  };

  if (loading && view === 'jobs') {
    return (
      <div className="min-h-screen bg-[#0B1120] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1120] text-slate-100">
      {/* Header */}
      <div className="bg-slate-900/50 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                {view === 'jobs' && 'My Job Postings'}
                {view === 'candidates' && `Candidates - ${selectedJob?.title}`}
                {view === 'report' && 'Interview Report'}
              </h1>
              <p className="text-slate-400 mt-1">
                {view === 'jobs' && 'Manage your job postings and view candidate reports'}
                {view === 'candidates' && 'Review candidates who completed interviews'}
                {view === 'report' && 'Comprehensive hiring decision report'}
              </p>
            </div>
            
            {view !== 'jobs' && (
              <button
                onClick={handleBack}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Jobs List View */}
        {view === 'jobs' && (
          <div className="space-y-4">
            {jobs.length === 0 ? (
              <div className="bg-slate-900/50 rounded-lg p-12 text-center border border-white/10">
                <p className="text-slate-400 mb-4">No job postings yet</p>
                <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
                  Create Job Posting
                </button>
              </div>
            ) : (
              jobs.map((job) => (
                <div
                  key={job.id}
                  className="bg-slate-900/50 rounded-lg border border-white/10 hover:border-white/20 transition-colors p-6"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-white mb-2">
                        {job.title}
                      </h3>
                      <p className="text-slate-400 text-sm mb-4 line-clamp-2">
                        {job.description}
                      </p>
                      
                      <div className="flex flex-wrap gap-4 text-sm">
                        <div>
                          <span className="text-slate-500">Location:</span>
                          <span className="text-slate-300 ml-2">{job.location || 'Remote'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Experience:</span>
                          <span className="text-slate-300 ml-2">{job.experience_years || 'Any'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Salary:</span>
                          <span className="text-slate-300 ml-2">{job.salary_range || 'Competitive'}</span>
                        </div>
                      </div>

                      {job.required_skills && job.required_skills.length > 0 && (
                        <div className="mt-4">
                          <p className="text-xs text-slate-500 mb-2">Required Skills:</p>
                          <div className="flex flex-wrap gap-2">
                            {job.required_skills.slice(0, 8).map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded text-xs"
                              >
                                {skill}
                              </span>
                            ))}
                            {job.required_skills.length > 8 && (
                              <span className="px-2 py-1 text-slate-500 text-xs">
                                +{job.required_skills.length - 8} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-4 ml-6">
                      <div className="text-center bg-slate-800/50 rounded-lg p-4">
                        <p className="text-3xl font-bold text-indigo-400">
                          {job.applicant_count || 0}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">Applicants</p>
                      </div>
                      
                      <button
                        onClick={() => handleViewCandidates(job)}
                        className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm font-medium"
                      >
                        View Candidates
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Candidates List View */}
        {view === 'candidates' && selectedJob && (
          <JobCandidatesList
            jobPostId={selectedJob.id}
            onViewReport={handleViewReport}
          />
        )}

        {/* Report View */}
        {view === 'report' && reportData && (
          <div>
            {/* Candidate Info Banner */}
            <div className="bg-slate-900/50 rounded-lg border border-white/10 p-6 mb-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-slate-500 text-sm">Candidate</p>
                  <p className="text-white font-semibold">{reportData.candidate_info?.name}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-sm">Email</p>
                  <p className="text-white">{reportData.candidate_info?.email}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-sm">Experience</p>
                  <p className="text-white">{reportData.candidate_info?.experience_years || 0} years</p>
                </div>
                <div>
                  <p className="text-slate-500 text-sm">Interview Date</p>
                  <p className="text-white">
                    {reportData.interview_info?.ended_at 
                      ? new Date(reportData.interview_info.ended_at).toLocaleDateString()
                      : 'N/A'
                    }
                  </p>
                </div>
              </div>

              {reportData.candidate_info?.skills && reportData.candidate_info.skills.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-slate-500 mb-2">Skills:</p>
                  <div className="flex flex-wrap gap-2">
                    {reportData.candidate_info.skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Full Report */}
            <RecruiterReportViewer
              report={reportData.recruiter_report}
              sessionId={reportData.session_id}
            />
          </div>
        )}
      </div>
    </div>
  );
}
