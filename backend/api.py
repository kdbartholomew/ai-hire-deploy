from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
import os
from job_matching import ResumeJobMatcher

app = FastAPI()

# CORS setup for frontend (like Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

matcher = ResumeJobMatcher(gcs_bucket_name="ai-hire-deploy-data")
matcher.load_from_cache(
    "jobs_with_embeddings.pkl",
    "jobs.csv"
)

@app.post("/match-jobs")
async def match_jobs(
    resume: UploadFile = File(...),
    similarity_threshold: float = Form(0.7)
):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    resume_bytes = await resume.read()

    try:
        results = matcher.find_matching_jobs(resume_bytes, similarity_threshold)
        return {"matches": results}
    except Exception as e:
        return {"error": str(e)}

@app.post("/match-candidates")
async def match_candidates(
    job_description: str = Form(...),
    similarity_threshold: float = Form(0.7),
    resumes: List[UploadFile] = File(...)
):
    for r in resumes:
        if r.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="All resumes must be PDFs.")
    
    resume_files = []
    for r in resumes:
        file_bytes = await r.read()
        resume_files.append({"filename": r.filename, "file_bytes": file_bytes})

    try:
        results = matcher.find_matching_candidates_dynamic(
            job_description, resume_files, similarity_threshold
        )
        return {"matches": results}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
