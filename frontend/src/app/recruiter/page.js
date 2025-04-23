"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RecruiterPage() {
  const router = useRouter();

  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFiles, setResumeFiles] = useState([]);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [matches, setMatches] = useState([]);
  const [noMatchesAboveThreshold, setNoMatchesAboveThreshold] = useState(false);
  const [loading, setLoading] = useState(false);

  function handleFilesChange(e) {
    setResumeFiles(Array.from(e.target.files));
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!jobTitle.trim()) return alert("Please enter a job title.");
    if (!jobDescription.trim()) return alert("Please enter a job description.");
    if (resumeFiles.length === 0) return alert("Please upload at least one resume.");

    setLoading(true);

    const formData = new FormData();
    formData.append("job_title", jobTitle);
    formData.append("job_description", jobDescription);
    formData.append("similarity_threshold", similarityThreshold);
    resumeFiles.forEach((file) => formData.append("resumes", file));

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/match-candidates`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) throw new Error("Failed to get candidate matches.");

      const data = await response.json();
      const matchesData = data.matches || [];

      const hasStrongMatch = matchesData.some((m) => m.similarity >= similarityThreshold);
      setNoMatchesAboveThreshold(!hasStrongMatch);
      setMatches(matchesData);
    } catch (error) {
      alert(error.message);
    }

    setLoading(false);
  }

  return (
    <main className="container">
      {/* Navigation Buttons */}
      <div style={{ marginBottom: "1rem" }}>
        <button
          className="btn btn-home"
          onClick={() => router.push("/")}
        >
          Home
        </button>
        <button
          className="btn btn-applicant"
          style={{ marginLeft: "1rem" }}
          onClick={() => router.push("/applicant")}
        >
          Go to Applicant Page
        </button>
      </div>

      <h1 className="title">Recruiter Candidate Matcher</h1>

      <form className="form" onSubmit={handleSubmit}>
        <label className="label">
          Job Title:
          <input
            className="input"
            type="text"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Software Engineer"
            required
          />
        </label>

        <label className="label">
          Job Description:
          <textarea
            className="textarea"
            rows={6}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Describe the job role here..."
            required
          />
        </label>

        <label className="label">
          Upload Resumes (PDFs):
          <input
            className="fileInput"
            type="file"
            accept="application/pdf"
            multiple
            onChange={handleFilesChange}
            required
          />
        </label>

        <label className="label">
          Similarity Threshold (0 to 1):
          <input
            className="input"
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={similarityThreshold}
            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
          />
        </label>

        <button className="button" type="submit" disabled={loading}>
          {loading ? "Matching..." : "Find Candidates"}
        </button>
      </form>

      <section className="results">
        <h2>Candidate Matches</h2>

        {matches.length === 0 && <p>No matches yet.</p>}

        {matches.length > 0 && (
          <>
            {noMatchesAboveThreshold ? (
              <p className="warning">
                ⚠️ No candidates met the similarity threshold of {similarityThreshold}. Showing the top{" "}
                {matches.length} most similar candidates instead.
              </p>
            ) : (
              <p className="success">
                Showing candidates who meet your threshold of {similarityThreshold}.
              </p>
            )}

            <ul className="matchList">
              {matches.map(({ resume_file, similarity }, idx) => (
                <li key={idx} className="matchItem">
                  <strong>{resume_file}</strong> — Similarity: {(similarity * 100).toFixed(2)}%
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </main>
  );
}
