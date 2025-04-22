# job_matching.py

import gensim
from gensim.models import Word2Vec
import numpy as np
import pandas as pd
import fitz
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Union
import os

class ResumeJobMatcher:
    def __init__(self, vector_size: int = 100, window: int = 5, min_count: int = 1, 
                 workers: int = 4, epochs: int = 10):
        """
        Initialize the ResumeJobMatcher with Word2Vec parameters.
        """
        self.model = None
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.workers = workers
        self.epochs = epochs
        self.job_desc_df = None
        
    def load_job_data(self, csv_path: str) -> None:
        """
        Load and preprocess job posting data from CSV.
        """
        job_posts = pd.read_csv(csv_path)
        self.job_desc_df = job_posts[["description", "job_id"]].dropna()
        self.job_desc_df["tokenized"] = self.job_desc_df["description"].apply(
            lambda desc: desc.lower().split()
        )
        self._train_word2vec()
        self._generate_job_embeddings()

    def _train_word2vec(self) -> None:
        """
        Train Word2Vec model on job descriptions.
        """
        self.model = Word2Vec(
            self.job_desc_df["tokenized"],
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            workers=self.workers,
            epochs=self.epochs
        )

    def _get_document_vector(self, words: List[str]) -> np.ndarray:
        """
        Create document embedding by averaging word vectors.
        """
        vectors = [self.model.wv[word] for word in words if word in self.model.wv]
        return np.mean(vectors, axis=0) if vectors else np.zeros(self.vector_size)

    def _generate_job_embeddings(self) -> None:
        """
        Generate embeddings for all job descriptions.
        """
        self.job_desc_df["embedding"] = self.job_desc_df["tokenized"].apply(
            lambda tokens: self._get_document_vector(tokens)
        )

    def process_resume(self, pdf_path: str) -> np.ndarray:
        """
        Process a single resume and return its embedding.
        """
        try:
            pdf_document = fitz.open(pdf_path)
            text = " ".join(page.get_text() for page in pdf_document)
            tokens = text.lower().split()
            return self._get_document_vector(tokens)
        except Exception as e:
            raise Exception(f"Error processing resume {pdf_path}: {e}")

    def find_matching_jobs(self, resume_path: str, similarity_threshold: float = 0.9) -> pd.DataFrame:
        """
        Find matching jobs for a single resume above the similarity threshold.
        """
        resume_embedding = self.process_resume(resume_path)
        
        self.job_desc_df["similarity"] = self.job_desc_df["embedding"].apply(
            lambda job_emb: cosine_similarity([resume_embedding], [job_emb])[0][0]
        )
        
        matches = self.job_desc_df[self.job_desc_df["similarity"] >= similarity_threshold]
        return matches[["job_id", "description", "similarity"]].sort_values(
            by="similarity", ascending=False
        )

    def find_matching_candidates(self, job_id: int, resume_folder: str, 
                               similarity_threshold: float = 0.9) -> List[Dict]:
        """
        Find matching candidates for a specific job posting above the similarity threshold.
        """
        job_posting = self.job_desc_df[self.job_desc_df["job_id"] == job_id]
        if job_posting.empty:
            raise ValueError(f"Job ID {job_id} not found")
            
        job_embedding = job_posting["embedding"].iloc[0]
        
        candidates = []
        for resume_file in os.listdir(resume_folder):
            if resume_file.endswith('.pdf'):
                resume_path = os.path.join(resume_folder, resume_file)
                try:
                    resume_embedding = self.process_resume(resume_path)
                    similarity = cosine_similarity([job_embedding], [resume_embedding])[0][0]
                    
                    if similarity >= similarity_threshold:
                        candidates.append({
                            "resume_file": resume_file,
                            "similarity": similarity
                        })
                except Exception as e:
                    print(f"Error processing {resume_file}: {e}")
                    
        return sorted(candidates, key=lambda x: x["similarity"], reverse=True)
    
    def save_model_and_embeddings(self, model_path: str, embed_path: str):
        self.model.save(model_path)
        self.job_desc_df.to_pickle(embed_path)

    def load_from_cache(self, model_path: str, embed_path: str):
        self.model = Word2Vec.load(model_path)
        self.job_desc_df = pd.read_pickle(embed_path)


def main():
    # Initialize the matcher
    matcher = ResumeJobMatcher()
    
    # Get job postings CSV path from user
    while True:
        jobs_csv_path = input("Enter the path to your job postings CSV file: ").strip()
        try:
            matcher.load_job_data(jobs_csv_path)
            break
        except Exception as e:
            print(f"Error loading job data: {e}")
            print("Please try again with a valid CSV file path.")
    
    # User selection menu
    while True:
        print("\nSelect your role:")
        print("1. Job Seeker")
        print("2. Recruiter")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "3":
            break
            
        if choice == "1":
            # Job seeker flow
            resume_path = input("Enter the path to your resume (PDF): ").strip()
            while True:
                try:
                    threshold = float(input("Enter minimum similarity threshold (0.0-1.0): ").strip())
                    if 0 <= threshold <= 1:
                        break
                    print("Please enter a value between 0.0 and 1.0")
                except ValueError:
                    print("Please enter a valid number between 0.0 and 1.0")
            
            try:
                matching_jobs = matcher.find_matching_jobs(resume_path, threshold)
                if matching_jobs.empty:
                    print("\nNo matching jobs found above the threshold.")
                else:
                    print("\nMatching jobs:")
                    for _, job in matching_jobs.iterrows():
                        print(f"\nJob ID: {job['job_id']}")
                        print(f"Similarity: {job['similarity']:.2%}")
                        print(f"Description: {job['description'][:200]}...")
            except Exception as e:
                print(f"Error processing resume: {e}")
                
        elif choice == "2":
            # Recruiter flow
            while True:
                try:
                    job_id = int(input("Enter the job ID to match candidates for: ").strip())
                    break
                except ValueError:
                    print("Please enter a valid job ID (number)")
            
            resume_folder = input("Enter the path to the folder containing resumes: ").strip()
            
            while True:
                try:
                    threshold = float(input("Enter minimum similarity threshold (0.0-1.0): ").strip())
                    if 0 <= threshold <= 1:
                        break
                    print("Please enter a value between 0.0 and 1.0")
                except ValueError:
                    print("Please enter a valid number between 0.0 and 1.0")
            
            try:
                matching_candidates = matcher.find_matching_candidates(job_id, resume_folder, threshold)
                if not matching_candidates:
                    print("\nNo matching candidates found above the threshold.")
                else:
                    print("\nMatching candidates:")
                    for candidate in matching_candidates:
                        print(f"\nResume: {candidate['resume_file']}")
                        print(f"Similarity: {candidate['similarity']:.2%}")
            except Exception as e:
                print(f"Error finding candidates: {e}")
        
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()











#     To use this with a UI, you can:
# Create an instance of ResumeJobMatcher
# Load the job data once at startup
# Call the appropriate method based on whether it's a job seeker or recruiter using the system
# For example, in your UI code you could do:
# # Initialize the matcher once
# matcher = ResumeJobMatcher()
# matcher.load_job_data("your_jobs.csv")

# # For job seekers
# def handle_job_seeker_request(resume_path: str, min_similarity: float):
#     matches = matcher.find_matching_jobs(resume_path, min_similarity)
#     return matches

# # For recruiters
# def handle_recruiter_request(job_id: int, resume_folder: str, min_similarity: float):
#     matches = matcher.find_matching_candidates(job_id, resume_folder, min_similarity)
#     return matches
