/**
 * Resume Upload Component
 * Clean White SaaS Theme
 */

import { useState, useRef } from 'react';
import resumeService from '@/services/resumeService';
import { formatApiDetail } from '@/utils/formatApiDetail';
import { Upload, FileText, CheckCircle2, AlertCircle, X, Sparkles } from 'lucide-react';

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
      setError('Please select a target job position first');
      return;
    }
    setUploading(true);
    setError('');
    try {
      const matchResult = await resumeService.matchResumeToJob(
        selectedJob.id,
        file,
        selectedJob.title
      );
      setResult(matchResult);
      if (onUploadSuccess) onUploadSuccess();
      if (onMatchResult) onMatchResult(matchResult);
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Upload className="h-4 w-4 text-blue-700" />
          Upload Resume & Match
        </h2>
        <span className="text-xs text-slate-400 font-medium">PDF or DOCX (max 10 MB)</span>
      </div>
      <p className="text-xs text-slate-500 mb-5">
        Upload your latest CV to match your skills directly against {selectedJob?.title || 'the selected role'}.
      </p>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-rose-800">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 transition-all duration-200
          ${
            dragActive
              ? 'border-indigo-500 bg-indigo-50/50'
              : file
                ? 'border-blue-500/80 bg-blue-50/40'
                : 'border-slate-200 bg-slate-50/50 hover:border-slate-300 hover:bg-slate-50'
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
        <div
          className={`mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border transition-colors ${
            file ? 'bg-blue-100 text-blue-700 border-blue-200' : 'bg-white text-slate-400 border-slate-200 shadow-2xs'
          }`}
        >
          <FileText className="h-6 w-6" />
        </div>

        {file ? (
          <div className="text-center">
            <p className="text-xs sm:text-sm font-bold text-slate-900">{file.name}</p>
            <p className="mt-0.5 text-xs text-slate-400 font-medium">
              {(file.size / 1024 / 1024).toFixed(2)} MB · Click to choose different file
            </p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-xs sm:text-sm font-semibold text-slate-700">
              Drag & drop your resume here, or <span className="text-blue-700 underline">browse files</span>
            </p>
            <p className="mt-1 text-[11px] text-slate-400">Supports PDF, DOCX format</p>
          </div>
        )}
      </div>

      {/* Upload button */}
      <button
        type="button"
        onClick={handleUpload}
        disabled={!file || uploading || !selectedJob}
        className="mt-4 w-full rounded-xl bg-blue-700 hover:bg-blue-800 py-2.5 text-xs sm:text-sm font-semibold text-white transition shadow-xs disabled:cursor-not-allowed disabled:opacity-50"
      >
        {uploading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Analyzing & Matching Skills…
          </span>
        ) : (
          'Upload & Match Resume'
        )}
      </button>

      {/* Success result */}
      {result && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/80 p-3.5 flex items-center gap-2 text-xs font-semibold text-emerald-800">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>Resume parsed and skill match calculated!</span>
        </div>
      )}
    </div>
  );
}
