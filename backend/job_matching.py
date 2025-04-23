import os
import numpy as np
import pandas as pd
import fitz
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from google.cloud import storage

class ResumeJobMatcher:
    def __init__(self, gcs_bucket_name=None):
        self.job_desc_df = None
        self.job_titles_df = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.gcs_bucket_name = gcs_bucket_name

    def download_from_gcs(self, source_blob_name: str, destination_file_name: str):
        if not self.gcs_bucket_name:
            raise ValueError("GCS bucket name not set.")
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.gcs_bucket_name)
        blob = bucket.blob(source_blob_name)
        print(f"Downloading {source_blob_name} from bucket {self.gcs_bucket_name} to {destination_file_name} ...")
        blob.download_to_filename(destination_file_name)
        print("Download complete.")

    def load_from_cache(self, embed_filename: str, titles_csv_filename: str):
        # Files will be downloaded into working directory
        embed_path = os.path.join(os.getcwd(), os.path.basename(embed_filename))
        titles_csv_path = os.path.join(os.getcwd(), os.path.basename(titles_csv_filename))

        # Download from GCS if files not present locally
        if not os.path.exists(embed_path):
            self.download_from_gcs(embed_filename, embed_path)
        if not os.path.exists(titles_csv_path):
            self.download_from_gcs(titles_csv_filename, titles_csv_path)

        # Load embeddings and job titles
        self.job_desc_df = pd.read_pickle(embed_path)
        self.job_desc_df['embedding'] = self.job_desc_df['embedding'].apply(np.array)
        self.job_titles_df = pd.read_csv(titles_csv_path)[['job_id', 'title']]

    def _embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, normalize_embeddings=True)

    def process_resume_bytes(self, resume_bytes: bytes) -> np.ndarray:
        pdf_document = fitz.open(stream=resume_bytes, filetype="pdf")
        text = " ".join(page.get_text() for page in pdf_document)
        return self._embed_text(text)

    def find_matching_jobs(self, resume_bytes: bytes, similarity_threshold: float = 0.7) -> List[Dict]:
        if self.job_desc_df is None or self.job_titles_df is None:
            raise ValueError("Job data must be loaded first.")

        resume_emb = self.process_resume_bytes(resume_bytes).reshape(1, -1)
        job_emb_matrix = np.vstack(self.job_desc_df['embedding'].values)
        similarities = np.dot(job_emb_matrix, resume_emb.T).flatten()

        jobs_df = self.job_desc_df.copy()
        jobs_df['similarity'] = similarities
        jobs_df = jobs_df.merge(self.job_titles_df, on='job_id', how='left')

        filtered_df = jobs_df[jobs_df['similarity'] >= similarity_threshold]

        if filtered_df.empty:
            print("Sorry, no jobs match your resume above that threshold. Here are the top 10 jobs that match you:")
            top_jobs = jobs_df.sort_values(by='similarity', ascending=False).head(10)
            return top_jobs[['job_id', 'title', 'similarity']].to_dict(orient='records')
        else:
            filtered_df = filtered_df.sort_values(by='similarity', ascending=False)
            return filtered_df[['job_id', 'title', 'similarity']].to_dict(orient='records')

    def find_matching_candidates_dynamic(self, job_description: str, resumes: List[Dict[str, bytes]], similarity_threshold: float = 0.7) -> List[Dict]:
        job_emb = self._embed_text(job_description).reshape(1, -1)
        candidates = []

        for resume in resumes:
            filename = resume.get('filename')
            file_bytes = resume.get('file_bytes')
            try:
                resume_emb = self.process_resume_bytes(file_bytes).reshape(1, -1)
                similarity = float(np.dot(job_emb, resume_emb.T).flatten()[0])
                candidates.append({'resume_file': filename, 'similarity': similarity})
            except Exception as e:
                print(f"Error processing resume {filename}: {e}")

        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        filtered_candidates = [c for c in candidates if c['similarity'] >= similarity_threshold]

        if not filtered_candidates:
            print("⚠️ No candidates met the similarity threshold. Showing top matches instead.")
            return candidates[:10]
        else:
            return filtered_candidates
