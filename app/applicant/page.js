// File: app/applicant/page.js
'use client'; // Make this a client component

import React, { useState } from 'react';

const ApplicantPage = () => {
  const [resume, setResume] = useState(null);
  const [threshold, setThreshold] = useState(0.5); // Default threshold
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]);

  // Handles file input change
  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    // Basic validation for PDF type
    if (file && file.type === 'application/pdf') {
      setResume(file);
      setMessage(''); // Clear previous messages
    } else {
      setResume(null);
      setMessage('Please upload a PDF file.');
    }
  };

  // Handles threshold slider change
  const handleThresholdChange = (e) => {
    setThreshold(parseFloat(e.target.value));
  };

  // Converts a file object to a base64 string (including data URI prefix)
  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file); // Reads the file as a data URL (base64)
      reader.onload = () => resolve(reader.result);
      reader.onerror = (error) => reject(error);
    });
  };

  // Handles form submission
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default browser form submission

    // --- Client-side Validation ---
    if (!resume) {
      setMessage('Please upload a resume.');
      return;
    }
    // Threshold is inherently limited by the range input, but good to check
    if (threshold < 0 || threshold > 1) {
      setMessage('Threshold must be between 0 and 1.');
      return;
    }

    // --- Start API Call ---
    setIsLoading(true);
    setMessage('Processing your resume and finding matches...');
    setResults([]); // Clear previous results

    try {
      // Convert the selected PDF file to base64
      const base64Resume = await convertToBase64(resume);

      // Make the POST request to the Python backend API endpoint
      const response = await fetch('/api/match', { // Targets api/match.py on Vercel
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send resume as base64 string and the threshold value
        body: JSON.stringify({
          resume: base64Resume, // e.g., "data:application/pdf;base64,JVBERi0xLjc..."
          threshold: threshold
        }),
      });

      // --- Handle API Response ---
      if (!response.ok) {
        // Try to parse error message from backend if available
        let errorData;
        try {
          errorData = await response.json();
        } catch (parseError) {
          // If response is not JSON or empty
          throw new Error(`Server responded with status: ${response.status}`);
        }
        // Use error message from backend or provide a default
        throw new Error(errorData?.error || 'Something went wrong on the server.');
      }

      // Parse the successful JSON response (list of matching jobs)
      const data = await response.json();

      // --- Update UI based on results ---
      if (data.length === 0) {
        setMessage('No matching jobs found with the current threshold. Try lowering the threshold value.');
      } else {
        setResults(data); // Store the matching jobs in state
        setMessage(`Found ${data.length} matching job(s).`);
      }

    } catch (err) {
      console.error("Fetch error:", err); // Log the full error for debugging
      // Display user-friendly error message
      setMessage(`Error: ${err.message}`);
    } finally {
      // Ensure loading state is turned off whether success or error
      setIsLoading(false);
    }
  };

  // --- Render JSX ---
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6 text-center">Find Matching Jobs</h1>

      {/* Form Section */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <form onSubmit={handleSubmit}>
          {/* Resume Upload */}
          <div className="mb-6">
            <label htmlFor="resume-upload" className="block text-gray-700 text-sm font-bold mb-2">
              Upload Resume (PDF only):
            </label>
            <input
              type="file"
              id="resume-upload"
              accept=".pdf" // Restrict file picker to PDF
              onChange={handleResumeChange}
              required // Basic HTML5 validation
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          {/* Similarity Threshold Slider */}
          <div className="mb-6">
            <label htmlFor="threshold" className="block text-gray-700 text-sm font-bold mb-2">
              Similarity Threshold: <span className="font-semibold text-blue-600">{threshold.toFixed(2)}</span>
            </label>
            <input
              type="range"
              id="threshold"
              value={threshold}
              min="0"
              max="1"
              step="0.05" // Granularity of the slider
              onChange={handleThresholdChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0 (More Results)</span>
              <span>1 (Stricter Matches)</span>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={isLoading || !resume} // Disable if loading or no resume selected
              className={`px-6 py-2 rounded-md font-medium text-white transition duration-150 ease-in-out
                ${isLoading || !resume
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                }`}
            >
              {isLoading ? 'Processing...' : 'Find Matching Jobs'}
            </button>
          </div>
        </form>
      </div>

      {/* Status/Error Message Area */}
      {message && (
        <div className={`p-4 mb-6 rounded-md text-center ${message.includes('Error:') ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
          {message}
        </div>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <div className="results">
          <h2 className="text-2xl font-bold mb-4">Matching Jobs</h2>
          <div className="space-y-4">
            {results.map((job, index) => (
              <div className="job-card bg-white shadow rounded-lg p-6" key={job.job_id || index}> {/* Use job_id as key if available */}
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-semibold">Job ID: {job.job_id}</h3>
                   {/* Display Similarity Score */}
                   <div className="text-right">
                    <span className="font-medium text-gray-700">Match Score: </span>
                    <span className="text-blue-600 font-bold">{(job.similarity * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {/* Job Description Preview */}
                <div className="mt-4">
                  <h4 className="font-medium text-gray-700 mb-1">Job Description:</h4>
                  <p className="text-gray-600 text-sm">
                    {/* Show truncated description */}
                    {job.description.length > 300
                      ? `${job.description.substring(0, 300)}...`
                      : job.description}
                  </p>
                  {/* Simple 'Read More' using alert - could be improved with modal/expansion */}
                  {job.description.length > 300 && (
                    <button
                      onClick={() => alert(`Full Description (Job ID: ${job.job_id}):\n\n${job.description}`)} // Show full description in an alert
                      className="text-blue-600 text-sm mt-2 hover:underline focus:outline-none"
                    >
                      Read More
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicantPage; // Export the component as the default for the page route