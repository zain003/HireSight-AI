/**
 * Resume Upload Component
 */

import { useState, useRef } from 'react';
import resumeService from '@/services/resumeService';

export default function ResumeUpload({ selectedJob, onUploadSuccess, onMatchResult }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (selectedFile) => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    if (selectedFile && !allowedTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF or DOCX file');
      return;
    }
    if (selectedFile && selectedFile.size > 10485760) {
      setError('File size must be less than 10MB');
      return;
    }
    setFile(selectedFile);
    setError('');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }
    if (!selectedJob) {
      setError('Please select a job post');
      return;
    }
    setUploading(true);
    setError('');
    try {
      // Use matchResumeToJob to get skill match and profile update
      const matchResult = await resumeService.matchResumeToJob(selectedJob.id, file);
      setResult(matchResult);
      if (onUploadSuccess) onUploadSuccess();
      if (onMatchResult) onMatchResult(matchResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8 bg-white rounded-2xl shadow-card border border-deep-night/[0.06]">
      <h2 className="text-xl font-bold mb-1 text-deep-night">Upload Resume</h2>
      <p className="text-text-muted text-sm mb-6">PDF or DOCX — max 10 MB</p>

      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center py-10 px-6 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300
          ${dragActive
            ? 'border-neon-glow bg-neon-violet/[0.04]'
            : file
              ? 'border-neon-violet/30 bg-neon-violet/[0.02]'
              : 'border-deep-night/10 bg-surface-subtle hover:border-neon-violet/25 hover:bg-neon-violet/[0.02]'
          }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Icon */}
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors duration-300 ${file ? 'bg-neon-violet/10' : 'bg-deep-night/[0.04]'}`}>
          <svg className={`w-7 h-7 ${file ? 'text-neon-violet' : 'text-text-muted'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>

        {file ? (
          <div className="text-center">
            <p className="text-deep-night font-medium text-sm">{file.name}</p>
            <p className="text-text-muted text-xs mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-deep-night font-medium text-sm">
              Drop your resume here or <span className="text-neon-violet">browse</span>
            </p>
            <p className="text-text-muted text-xs mt-1">Supports PDF and DOCX</p>
          </div>
        )}
      </div>

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading || !selectedJob}
        className="w-full neon-btn py-3.5 rounded-xl font-semibold text-base tracking-wide mt-5 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {uploading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Matching skills...
          </span>
        ) : (
          'Upload & Match Resume'
        )}
      </button>

      {/* Success result */}
      {result && (
        <div className="mt-6 p-5 rounded-2xl border border-neon-violet/15 bg-neon-violet/[0.02] animate-slide-up">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-neon-violet/10 flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-neon-violet" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-deep-night">Resume Parsed Successfully</h3>
          </div>
        </div>
      )}
    </div>
  );
}
