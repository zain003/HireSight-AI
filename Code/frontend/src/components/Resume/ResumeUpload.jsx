/**
 * Resume Upload Component
 */
import { useState } from 'react';
import resumeService from '@/services/resumeService';

export default function ResumeUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (selectedFile && !allowedTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF or DOCX file');
      return;
    }

    // Validate file size (10MB)
    if (selectedFile && selectedFile.size > 10485760) {
      setError('File size must be less than 10MB');
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const data = await resumeService.uploadResume(file);
      setResult(data);
      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">Upload Resume</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="mb-4">
        <label className="block text-gray-700 mb-2">
          Select Resume (PDF or DOCX)
        </label>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
      >
        {uploading ? 'Uploading...' : 'Upload & Parse Resume'}
      </button>

      {result && (
        <div className="mt-6 p-4 bg-green-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3 text-green-800">
            ✓ Resume Parsed Successfully
          </h3>
          
          <div className="mb-3">
            <p className="font-semibold text-gray-700">Domain:</p>
            <p className="text-gray-600">{result.domain}</p>
          </div>

          <div className="mb-3">
            <p className="font-semibold text-gray-700">Skills Extracted:</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {result.skills.map((skill, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {result.experience?.summary && (
            <div>
              <p className="font-semibold text-gray-700">Experience:</p>
              <p className="text-gray-600 text-sm">{result.experience.summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
