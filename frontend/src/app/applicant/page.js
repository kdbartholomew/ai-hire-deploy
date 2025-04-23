"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ApplicantPage() {
  const router = useRouter();

  const [resumeFile, setResumeFile] = useState(null);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  // New state to show the inline warning message instead of alert popup
  const [showThresholdWarning, setShowThresholdWarning] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!resumeFile) return alert("Please upload a resume PDF.");

    setLoading(true);
    setShowThresholdWarning(false); // reset warning each submit

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("similarity_threshold", similarityThreshold);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/match-jobs`,
        {
          method: "POST",
          body: formData,
        }
      );
      if (!res.ok) throw new Error("Failed to fetch matching jobs.");
      const data = await res.json();
      setMatches(data.matches || []);

      if ((data.matches?.length || 0) > 0) {
        const topMatch = data.matches[0];
        // Show inline warning if top match similarity is below threshold
        if (topMatch.similarity < similarityThreshold) {
          setShowThresholdWarning(true);
        }
      } else {
        // No matches at all means show the warning too
        setShowThresholdWarning(true);
      }
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  }

  return (
    <div>
      {/* Navigation Buttons */}
      <div style={{ marginBottom: "1rem" }}>
        <button
          className="btn btn-home"
          onClick={() => router.push("/")}
        >
          Home
        </button>
        <button
          className="btn btn-recruiter"
          style={{ marginLeft: "1rem" }}
          onClick={() => router.push("/recruiter")}
        >
          Go to Recruiter Page
        </button>
      </div>

      <h1>Applicant Job Matcher</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Upload Resume (PDF):
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setResumeFile(e.target.files[0])}
            required
          />
        </label>
        <br />
        <label>
          Similarity Threshold (0 to 1):
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={similarityThreshold}
            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
          />
        </label>
        <br />
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Matching..." : "Find Jobs"}
        </button>
      </form>

      <h2>Job Matches</h2>
      {matches.length === 0 && <p>No matches yet.</p>}

      {/* Inline warning message */}
      {showThresholdWarning && (
        <div className="alert-message">
          No jobs matched your similarity threshold. Here are the 10 most similar jobs instead.
        </div>
      )}

      <ul>
        {matches.map(({ job_id, title, similarity }) => (
          <li key={job_id}>
            <strong>{title}</strong> — Similarity: {(similarity * 100).toFixed(2)}%
          </li>
        ))}
      </ul>
    </div>
  );
}
