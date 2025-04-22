# File: api/find_candidates.py
import json
import base64
import os
import tempfile
import traceback
import time
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
import fitz # PyMuPDF (ensure it's in requirements.txt)

# --- Global variables ---
model_instance = None
model_lock = False
model_error = None
MODEL_NAME = 'all-MiniLM-L6-v2' # Use the same model as for jobs

# --- Helper Function (can be moved to a shared lib later) ---
def _extract_text_from_pdf(pdf_path: str) -> str | None:
    """Extract text content from a PDF file."""
    try:
        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text("text")
        pdf_document.close()
        if not text.strip(): return None
        return ' '.join(text.split()) # Basic cleaning
    except Exception as e:
        print(f"Error processing PDF {os.path.basename(pdf_path)}: {e}")
        return None

# --- Initialize Model Safely (similar to matcher) ---
def initialize_model_safely():
    """Initialize the Sentence Transformer model ONCE."""
    global model_instance, model_lock, model_error

    if model_instance: return model_instance
    if model_error: raise model_error
    if model_lock: raise RuntimeError("Model initialization in progress.")

    model_lock = True
    print("--- Attempting Sentence Transformer Model Initialization ---")
    start_time = time.time()
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"--- Using device: {device}")
        temp_model = SentenceTransformer(MODEL_NAME, device=device)
        model_instance = temp_model
        print(f"--- Model '{MODEL_NAME}' initialized successfully in {time.time() - start_time:.2f} seconds ---")
        return model_instance
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"--- FATAL ERROR during Model Initialization ---")
        print(error_details)
        model_error = RuntimeError(f"Model initialization failed: {e}")
        raise model_error
    finally:
        model_lock = False

# --- Vercel Response Helper ---
def create_response(status_code, body, is_json=True, headers=None):
    """Helper to create Vercel response structure with CORS."""
    response_headers = {
        "Access-Control-Allow-Origin": "*", # Be more specific in production
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        **(headers or {})
    }
    if is_json:
        response_headers["Content-Type"] = "application/json"
        body_content = json.dumps(body)
    else:
        body_content = body
    return {"statusCode": status_code, "headers": response_headers, "body": body_content}

# --- Main Vercel Handler ---
def handler(request):
    """Handle incoming requests for finding matching candidates."""
    http_method = request.get("httpMethod", "POST").upper() # Default to POST for simplicity

    if http_method == "OPTIONS":
        print("--- Handling OPTIONS request ---")
        return create_response(200, "")

    if http_method != "POST":
        print(f"--- Method not allowed: {http_method} ---")
        return create_response(405, {"error": "Method Not Allowed"})

    print(f"\n--- Received POST request to find_candidates at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    request_start_time = time.time()
    request_id = request.get("headers", {}).get("x-vercel-id", "N/A")
    print(f"Request ID: {request_id}")

    temp_files_to_clean = [] # Keep track of temp files created

    try:
        # --- Get Model Instance ---
        print("Getting model instance...")
        current_model = initialize_model_safely()
        model_device = current_model.device
        print(f"Model instance ready on device: {model_device}")

        # --- Parse Request Body ---
        print("Parsing request body...")
        try:
            body_raw = request.get("body")
            if not body_raw: raise ValueError("Request body is missing.")
            # Vercel might base64 encode the body if not Content-Type: application/json
            if request.get("isBase64Encoded"):
                body_decoded = base64.b64decode(body_raw).decode('utf-8')
                payload = json.loads(body_decoded)
            elif isinstance(body_raw, str):
                 payload = json.loads(body_raw)
            elif isinstance(body_raw, dict): # Already parsed by Vercel?
                 payload = body_raw
            else:
                 raise TypeError("Unexpected body type.")
            print("Request body parsed successfully.")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing request body: {e}")
            return create_response(400, {"error": f"Invalid or missing request payload: {e}"})

        # --- Extract Data from Payload ---
        job_description = payload.get("job_description")
        resumes_data = payload.get("resumes_data") # Expecting list of {filename, content}
        threshold_str = payload.get("threshold")

        # --- Input Validation ---
        print("Validating input...")
        if not job_description or not isinstance(job_description, str) or not job_description.strip():
            return create_response(400, {"error": "Missing or empty job_description"})
        if not resumes_data or not isinstance(resumes_data, list) or len(resumes_data) == 0:
            return create_response(400, {"error": "Missing or empty resumes_data list"})
        if not all(isinstance(item, dict) and 'filename' in item and 'content' in item for item in resumes_data):
             return create_response(400, {"error": "Invalid format in resumes_data list. Expected list of {'filename': str, 'content': str}"})

        try:
            threshold = float(threshold_str if threshold_str is not None else 0.5)
            if not (0.0 <= threshold <= 1.0): threshold = 0.5
        except (ValueError, TypeError):
            threshold = 0.5
        print(f"Using threshold: {threshold:.2f}")
        print(f"Processing {len(resumes_data)} resumes...")

        # --- Embed Job Description ---
        print("Embedding job description...")
        jd_encode_start = time.time()
        jd_embedding = current_model.encode(
            job_description,
            convert_to_tensor=True,
            normalize_embeddings=True # Crucial for cosine similarity
        ).to(model_device)
        print(f"Job description embedded in {time.time() - jd_encode_start:.2f} seconds.")

        # --- Process Each Resume ---
        candidate_results = []
        for i, resume_item in enumerate(resumes_data):
            filename = resume_item.get('filename', f'resume_{i+1}.pdf') # Fallback filename
            base64_content = resume_item.get('content')
            temp_file_path = None
            print(f"\nProcessing resume {i+1}/{len(resumes_data)}: {filename}")

            if not base64_content or not isinstance(base64_content, str):
                 print(f"Skipping resume {filename}: Missing or invalid base64 content.")
                 continue

            try:
                # Decode Base64 (strip data URI scheme if present)
                if base64_content.startswith('data:'):
                    base64_content = base64_content.split(",", 1)[1]
                resume_bytes = base64.b64decode(base64_content)

                # Save to Temp File
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir="/tmp") as tmp:
                    tmp.write(resume_bytes)
                    temp_file_path = tmp.name
                temp_files_to_clean.append(temp_file_path) # Add to cleanup list
                print(f"Saved temp file: {temp_file_path}")

                # Extract Text
                resume_text = _extract_text_from_pdf(temp_file_path)
                if not resume_text:
                    print(f"Skipping resume {filename}: Could not extract text.")
                    continue

                # Embed Resume Text
                print("Embedding resume text...")
                resume_encode_start = time.time()
                resume_embedding = current_model.encode(
                    resume_text,
                    convert_to_tensor=True,
                    normalize_embeddings=True
                ).to(model_device)
                print(f"Resume embedded in {time.time() - resume_encode_start:.2f} seconds.")

                # Calculate Similarity
                similarity_score = util.cos_sim(jd_embedding, resume_embedding)[0][0].item() # Get single float value
                print(f"Similarity score: {similarity_score:.4f}")

                # Store result if above threshold
                if similarity_score >= threshold:
                    candidate_results.append({
                        "filename": filename,
                        "similarity": float(similarity_score) # Ensure float for JSON
                    })
                    print(f"Added {filename} to potential matches.")
                else:
                    print(f"Resume {filename} below threshold.")

            except fitz.fitz.FileNotFoundError:
                 print(f"Skipping resume {filename}: PDF library error (maybe corrupted file).")
            except (base64.binascii.Error, ValueError) as e:
                 print(f"Skipping resume {filename}: Invalid base64 data - {e}")
            except Exception as e:
                print(f"Error processing resume {filename}: {e}")
                traceback.print_exc() # Log detailed error for debugging
            finally:
                 # Optional: Clean up temp file immediately (or rely on finally block below)
                 # if temp_file_path and os.path.exists(temp_file_path):
                 #     os.remove(temp_file_path)
                 pass # Rely on main finally block

        # --- Rank and Return Results ---
        print("\nRanking candidates...")
        ranked_candidates = sorted(candidate_results, key=lambda x: x['similarity'], reverse=True)

        print(f"Returning {len(ranked_candidates)} matching candidates.")
        total_request_time = time.time() - request_start_time
        print(f"--- Request ID {request_id} (find_candidates) handled successfully in {total_request_time:.2f} seconds ---")
        return create_response(200, ranked_candidates)

    # --- Catch ALL Other Exceptions ---
    except RuntimeError as e: # Catch initialization errors
         print(f"RUNTIME ERROR: {e}")
         return create_response(500, {"error": "Server initialization failed."})
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"--- UNEXPECTED ERROR processing request ID {request_id} (find_candidates) ---")
        print(error_details)
        return create_response(500, {"error": "An unexpected internal server error occurred."})
    finally:
        # --- GUARANTEED Clean up ALL Temp Files ---
        print(f"Cleaning up {len(temp_files_to_clean)} temporary files...")
        cleaned_count = 0
        for file_path in temp_files_to_clean:
             if file_path and os.path.exists(file_path):
                 try:
                     os.remove(file_path)
                     cleaned_count += 1
                 except OSError as e:
                     print(f"Warning: Could not delete temporary file {file_path}: {e}")
        print(f"Cleaned up {cleaned_count} files.")