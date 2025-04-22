// File: app/recruiter/page.js
'use client'; // This component requires client-side interaction (state, events)

import React, { useState } from 'react';

const RecruiterPage = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [resumes, setResumes] = useState([]); // Store File objects
  const [threshold, setThreshold] = useState(0.5); // Default threshold
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]); // Store ranked candidate results

  // Handles job description textarea change
  const handleJDChange = (e) => {
    setJobDescription(e.target.value);
  };

  // Handles file input change for multiple resumes
  const handleResumeChange = (e) => {
    // e.target.files is a FileList, convert it to an array
    const files = Array.from(e.target.files);
    // Simple validation: check if all are PDFs (optional but good practice)
    const nonPdfs = files.filter(file => file.type !== 'application/pdf');
    if (nonPdfs.length > 0) {
      setMessage('Warning: Some selected files are not PDFs and will be ignored.');
      // Filter out non-PDFs if you want to be strict
      setResumes(files.filter(file => file.type === 'application/pdf'));
    } else {
       setResumes(files);
       setMessage(''); // Clear message if all are PDFs
    }
    // Optionally display selected file names
    if(files.length > 0) {
        setMessage(`Selected ${files.length} file(s): ${files.map(f => f.name).join(', ')}`);
    }
  };

  // Handles threshold slider change
  const handleThresholdChange = (e) => {
    setThreshold(parseFloat(e.target.value));
  };

  // Converts a single file object to a base64 string
  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result); // result includes data URI prefix
      reader.onerror = (error) => reject(error);
    });
  };

  // Handles form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // --- Client-side Validation ---
    if (!jobDescription.trim()) {
      setMessage('Please enter a job description.');
      return;
    }
    if (resumes.length === 0) {
      setMessage('Please upload at least one resume.');
      return;
    }
    if (threshold < 0 || threshold > 1) {
      setMessage('Threshold must be between 0 and 1.');
      return;
    }

    // --- Start API Call ---
    setIsLoading(true);
    setMessage(`Processing ${resumes.length} resume(s)...`);
    setResults([]); // Clear previous results

    try {
      // Convert all resume files to base64 strings concurrently
      const base64ResumesPromises = resumes.map(file => convertToBase64(file));
      const base64Resumes = await Promise.all(base64ResumesPromises);

      // Get filenames to send along for identification in results
      const resumeFilenames = resumes.map(file => file.name);

      // Make the POST request to the new backend API endpoint
      const response = await fetch('/api/find_candidates', { // <--- NEW API ROUTE
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_description: jobDescription,
          // Send an array of objects, each with filename and base64 data
          resumes_data: base64Resumes.map((data, index) => ({
            filename: resumeFilenames[index],
            content: data // Base64 string with data URI prefix
          })),
          threshold: threshold
        }),
      });

      // --- Handle API Response ---
      if (!response.ok) {
        let errorData;
        try { errorData = await response.json(); }
        catch (parseError) { throw new Error(`Server responded with status: ${response.status}`); }
        throw new Error(errorData?.error || 'Something went wrong on the server.');
      }

      const data = await response.json(); // Expecting [{ filename: '...', similarity: ... }, ...]

      // --- Update UI based on results ---
      if (data.length === 0) {
        setMessage('No matching candidates found above the threshold.');
      } else {
        setResults(data); // Store the ranked candidates
        setMessage(`Found ${data.length} potential candidate(s).`);
      }

    } catch (err) {
      console.error("Fetch error:", err);
      setMessage(`Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Render JSX ---
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6 text-center">Find Matching Candidates</h1>

      {/* Form Section */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <form onSubmit={handleSubmit}>
          {/* Job Description Textarea */}
          <div className="mb-6">
            <label htmlFor="job-description" className="block text-gray-700 text-sm font-bold mb-2">
              Job Description:
            </label>
            <textarea
              id="job-description"
              rows="8"
              value={jobDescription}
              onChange={handleJDChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Paste the full job description here..."
            />
          </div>

          {/* Resume Upload (Multiple) */}
          <div className="mb-6">
            <label htmlFor="resume-upload" className="block text-gray-700 text-sm font-bold mb-2">
              Upload Candidate Resumes (PDF only):
            </label>
            <input
              type="file"
              id="resume-upload"
              accept=".pdf"
              multiple // Allow multiple file selection
              onChange={handleResumeChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
            />
             {/* Display selected filenames if needed */}
             {resumes.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                    Selected: {resumes.map(f => f.name).join(', ')}
                </p>
             )}
          </div>

          {/* Similarity Threshold Slider */}
          <div className="mb-6">
            <label htmlFor="threshold" className="block text-gray-700 text-sm font-bold mb-2">
              Minimum Similarity Threshold: <span className="font-semibold text-green-600">{threshold.toFixed(2)}</span>
            </label>
            <input
              type="range"
              id="threshold"
              value={threshold}
              min="0"
              max="1"
              step="0.05"
              onChange={handleThresholdChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600" // Style slider track
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0 (Include More Candidates)</span>
              <span>1 (Stricter Matches)</span>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={isLoading || resumes.length === 0 || !jobDescription.trim()}
              className={`px-6 py-2 rounded-md font-medium text-white transition duration-150 ease-in-out
                ${isLoading || resumes.length === 0 || !jobDescription.trim()
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'
                }`}
            >
              {isLoading ? 'Processing...' : 'Find Candidates'}
            </button>
          </div>
        </form>
      </div>

      {/* Status/Error Message Area */}
      {message && (
         <div className={`p-4 mb-6 rounded-md text-center ${message.includes('Error:') ? 'bg-red-100 text-red-700' : (message.includes('Warning:') ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700')}`}>
           {/* Use different background based on message type */}
           {message}
         </div>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <div className="results">
          <h2 className="text-2xl font-bold mb-4">Matching Candidates</h2>
          <div className="overflow-x-auto">
             <table className="min-w-full bg-white shadow rounded-lg">
                <thead>
                    <tr className="bg-gray-100">
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resume File</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Similarity Score</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {results.map((candidate, index) => (
                        <tr key={candidate.filename || index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{index + 1}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{candidate.filename}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-semibold">
                                {(candidate.similarity * 100).toFixed(1)}%
                            </td>
                        </tr>
                    ))}
                </tbody>
             </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecruiterPage;