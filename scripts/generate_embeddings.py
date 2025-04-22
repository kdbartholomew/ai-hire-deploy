# scripts/generate_embeddings.py
import pandas as pd
from sentence_transformers import SentenceTransformer
import pickle
import os
import time

# --- Configuration ---
# Path relative to the script's location
INPUT_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'api', 'jobs.csv')
OUTPUT_PICKLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'api', 'jobs_with_embeddings.pkl')
MODEL_NAME = 'all-MiniLM-L6-v2' # Efficient and effective model

# --- Main Script ---
print(f"--- Starting Embedding Generation ---")
print(f"Using model: {MODEL_NAME}")

try:
    start_time = time.time()
    print(f"Loading model '{MODEL_NAME}'...")
    # Specify cache folder if desired, e.g., cache_folder='./cached_models'
    model = SentenceTransformer(MODEL_NAME)
    print(f"Model loaded in {time.time() - start_time:.2f} seconds.")

    print(f"Loading job data from: {INPUT_CSV_PATH}")
    if not os.path.exists(INPUT_CSV_PATH):
        raise FileNotFoundError(f"Cannot find input CSV: {INPUT_CSV_PATH}")

    job_posts = pd.read_csv(INPUT_CSV_PATH)

    # --- Data Validation and Cleaning ---
    if 'job_id' not in job_posts.columns or 'description' not in job_posts.columns:
        raise ValueError("CSV must contain 'job_id' and 'description' columns")

    print(f"Original job count: {len(job_posts)}")
    # Drop rows with missing descriptions, as they cannot be embedded
    job_posts = job_posts.dropna(subset=['description'])
    # Ensure description is string type
    job_posts['description'] = job_posts['description'].astype(str)
    # Optionally filter out very short descriptions if they are noise
    # job_posts = job_posts[job_posts['description'].str.len() > 20]
    print(f"Jobs after cleaning (non-empty description): {len(job_posts)}")

    if len(job_posts) == 0:
         raise ValueError("No valid job descriptions found in the CSV after cleaning.")

    # --- Generate Embeddings ---
    texts_to_encode = job_posts['description'].tolist()
    print(f"Generating embeddings for {len(texts_to_encode)} job descriptions...")
    start_time = time.time()
    # Use normalize_embeddings=True for cosine similarity
    job_embeddings = model.encode(texts_to_encode, show_progress_bar=True, normalize_embeddings=True)
    print(f"Embeddings generated in {time.time() - start_time:.2f} seconds.")

    # --- Store Embeddings ---
    # Store embeddings as lists in the DataFrame for easier serialization with pickle
    job_posts['embedding'] = [emb.tolist() for emb in job_embeddings]

    # --- Save Data ---
    print(f"Saving job data with embeddings to: {OUTPUT_PICKLE_PATH}")
    os.makedirs(os.path.dirname(OUTPUT_PICKLE_PATH), exist_ok=True)
    with open(OUTPUT_PICKLE_PATH, 'wb') as f:
        pickle.dump(job_posts[['job_id', 'description', 'embedding']], f) # Save only needed columns

    print(f"--- Pre-computation finished successfully! ---")

except FileNotFoundError as e:
     print(f"\nERROR: Input file not found. {e}")
     print("Please ensure 'api/jobs.csv' exists relative to the project root.")
except ValueError as e:
     print(f"\nERROR: Data validation failed. {e}")
except Exception as e:
     print(f"\nAn unexpected error occurred: {e}")
     import traceback
     traceback.print_exc()