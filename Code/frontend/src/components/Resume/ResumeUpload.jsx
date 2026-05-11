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
      const matchResult = await resumeService.matchResumeToJob(
        selectedJob.id,
        file,
        selectedJob.title
      );
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
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-sm">
      <h2 className="mb-1 text-xl font-bold text-white">Upload Resume</h2>
      <p className="mb-6 text-sm text-slate-300">PDF or DOCX - max 10 MB</p>

      {error && (
        <div className="mb-5 rounded-xl border border-red-400/30 bg-red-500/10 p-3.5 text-sm text-red-300">
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
        className={`relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 transition-all duration-300
          ${dragActive
            ? 'border-indigo-400 bg-indigo-500/10'
            : file
              ? 'border-indigo-400/70 bg-indigo-500/10'
              : 'border-white/20 bg-slate-950/50 hover:border-indigo-400/60 hover:bg-indigo-500/10'
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
        <div className={`mb-4 flex h-14 w-14 items-center justify-center rounded-2xl transition-colors duration-300 ${file ? 'bg-indigo-500/20' : 'bg-white/10'}`}>
          <svg className={`h-7 w-7 ${file ? 'text-indigo-300' : 'text-slate-300'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>

        {file ? (
          <div className="text-center">
            <p className="text-sm font-medium text-white">{file.name}</p>
            <p className="mt-1 text-xs text-slate-300">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-sm font-medium text-slate-100">
              Drop your resume here or <span className="text-indigo-300">browse</span>
            </p>
            <p className="mt-1 text-xs text-slate-300">Supports PDF and DOCX</p>
          </div>
        )}
      </div>

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading || !selectedJob}
        className="mt-5 w-full rounded-xl bg-indigo-500 py-3.5 text-base font-semibold tracking-wide text-white hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-40"
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
        <div className="mt-6 animate-slide-up rounded-2xl border border-indigo-400/30 bg-indigo-500/10 p-5">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20">
              <svg className="h-3.5 w-3.5 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white">Resume Parsed Successfully</h3>
          </div>
        </div>
      )}
    </div>
  );
}
