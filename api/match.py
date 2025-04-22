# # api/match.py


# File: api/match.py (Temporary for Testing)
import json
import time
import os # Import os just to be sure imports work

print(f"--- Python script api/match.py loaded at {time.strftime('%Y-%m-%d %H:%M:%S')} ---") # Check if file loads

def create_response(status_code, body, is_json=True, headers=None):
    # Basic response helper
    response_headers = {
        "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",**(headers or {})}
    if is_json:
        response_headers["Content-Type"] = "application/json"
        body_content = json.dumps(body)
    else: body_content = body
    return {"statusCode": status_code, "headers": response_headers, "body": body_content}

def handler(request):
    # Vercel passes request info as a dict-like object
    http_method = request.get("httpMethod", "POST").upper()
    path = request.get("path", "Unknown path")

    print(f"--- >>> Handler in api/match.py invoked for path: {path} <<< ---") # Check if handler runs
    print(f"--- HTTP Method: {http_method} ---")

    # Handle CORS preflight OPTIONS request
    if http_method == "OPTIONS":
        print("--- Handling OPTIONS request ---")
        return create_response(200, "")

    # Handle actual POST request
    if http_method == "POST":
        print("--- Handling POST request ---")
        # Return simple success, ignore body for now
        try:
            # Try accessing request body if needed for debugging later
            # body_content = request.get('body', '{}')
            # print(f"--- Request Body (raw): {body_content}")
            pass
        except Exception as e:
             print(f"Error reading body: {e}")

        return create_response(200, {"message": "SUCCESS: Test /api/match endpoint reached!"})
    else:
        # Handle other methods if necessary, or return error
        print(f"--- Method {http_method} Not Allowed ---")
        return create_response(405, {"error": f"Method {http_method} Not Allowed"})

# Optional: Check if running directly (won't happen in Vercel context but useful for basic syntax check)
if __name__ == "__main__":
    print("This script is designed to be run by a serverless environment like Vercel.")



    
# import json
# import base64
# import os
# import tempfile
# from job_matching import ResumeJobMatcher # Import updated matcher
# import traceback
# import time

# # --- Global variables for model persistence ---
# matcher_instance = None
# initialization_lock = False # Simple lock for initialization
# initialization_error = None # Store initialization error

# # Define path to pre-computed data (relative to this file)
# PRECOMPUTED_DATA_PATH = os.path.join(os.path.dirname(__file__), "jobs_with_embeddings.pkl")

# def initialize_matcher_safely():
#     """Initialize the matcher ONCE using pre-computed data, with error handling."""
#     global matcher_instance, initialization_lock, initialization_error

#     if matcher_instance is not None:
#         # Already initialized successfully
#         return matcher_instance

#     if initialization_error is not None:
#         # Initialization previously failed
#         raise initialization_error

#     # Simple lock to prevent concurrent initialization attempts during cold start burst
#     if initialization_lock:
#         # Another request is initializing, wait briefly or raise?
#         # For Vercel, raising might be better to signal failure quickly
#         print("--- WARNING: Concurrent initialization attempt detected ---")
#         raise RuntimeError("Initialization in progress by another request.")

#     initialization_lock = True
#     print("--- Attempting ResumeJobMatcher Initialization ---")
#     start_time = time.time()
#     try:
#         if not os.path.exists(PRECOMPUTED_DATA_PATH):
#              raise FileNotFoundError(f"Required data file not found: {PRECOMPUTED_DATA_PATH}")

#         temp_matcher = ResumeJobMatcher() # Uses 'all-MiniLM-L6-v2' by default
#         temp_matcher.load_model_and_data(PRECOMPUTED_DATA_PATH)
#         # If successful, assign to global instance
#         matcher_instance = temp_matcher
#         print(f"--- Matcher initialization SUCCESSFUL in {time.time() - start_time:.2f} seconds ---")
#         return matcher_instance
#     except Exception as e:
#         # Store the error and print details
#         error_details = traceback.format_exc()
#         print(f"--- FATAL ERROR during Matcher Initialization ---")
#         print(error_details)
#         initialization_error = RuntimeError(f"Matcher initialization failed: {e}")
#         # Raise the stored error
#         raise initialization_error
#     finally:
#         # Release the lock regardless of success or failure
#         initialization_lock = False


# def create_response(status_code, body, is_json=True, headers=None):
#     """Helper to create Vercel response structure with CORS."""
#     response_headers = {
#         "Access-Control-Allow-Origin": "*", # Be more specific in production
#         "Access-Control-Allow-Methods": "POST, OPTIONS",
#         "Access-Control-Allow-Headers": "Content-Type",
#         **(headers or {}) # Allow adding custom headers
#     }
#     if is_json:
#         response_headers["Content-Type"] = "application/json"
#         body_content = json.dumps(body)
#     else:
#         body_content = body

#     return {
#         "statusCode": status_code,
#         "headers": response_headers,
#         "body": body_content
#     }

# def handler(request):
#     """Handle incoming requests for job matching."""
#     # Vercel might pass event/context differently, adapt if needed
#     # We assume 'request' is a dict-like object from Vercel's Python runtime
#     http_method = request.get("httpMethod", request.get("method", "UNKNOWN")).upper()

#     # CORS Preflight Request
#     if http_method == "OPTIONS":
#         print("--- Handling OPTIONS request ---")
#         return create_response(200, "")

#     # Ensure POST request
#     if http_method != "POST":
#         print(f"--- Method not allowed: {http_method} ---")
#         return create_response(405, {"error": "Method Not Allowed"})

#     print(f"\n--- Received POST request at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
#     request_start_time = time.time()
#     request_id = request.get("headers", {}).get("x-vercel-id", "N/A") # Get Vercel request ID if available
#     print(f"Request ID: {request_id}")

#     try:
#         # --- Initialization (runs only if needed) ---
#         print("Getting matcher instance...")
#         current_matcher = initialize_matcher_safely()
#         print("Matcher instance ready.")

#         # --- Parse Request Body ---
#         print("Parsing request body...")
#         try:
#             # Vercel typically puts the body in 'body' key
#             body_raw = request.get("body", None)
#             if body_raw is None:
#                  raise ValueError("Request body is missing.")

#             # Check if Vercel base64 encoded the body
#             if request.get("isBase64Encoded", False):
#                  print("Decoding base64 encoded body...")
#                  body_decoded = base64.b64decode(body_raw).decode('utf-8')
#                  form_data = json.loads(body_decoded)
#             else:
#                  # Assume body is already a string (or maybe parsed dict if content-type was right)
#                  if isinstance(body_raw, dict):
#                       form_data = body_raw # Already parsed?
#                  elif isinstance(body_raw, str):
#                       form_data = json.loads(body_raw)
#                  else:
#                       raise TypeError("Unexpected body type.")
#             print("Request body parsed successfully.")
#         except (json.JSONDecodeError, ValueError, TypeError) as e:
#             print(f"Error parsing request body: {e}")
#             # Log the raw body for debugging if possible (be careful with PII)
#             # print(f"Raw body: {body_raw}")
#             return create_response(400, {"error": f"Invalid or missing request payload: {e}"})

#         threshold_str = form_data.get("threshold")
#         resume_b64 = form_data.get("resume")

#         # --- Input Validation ---
#         print("Validating input...")
#         if not resume_b64 or not isinstance(resume_b64, str):
#             print("Error: Missing or invalid resume data (base64 string required).")
#             return create_response(400, {"error": "Missing or invalid resume data (base64 string required)"})

#         try:
#             threshold = float(threshold_str if threshold_str is not None else 0.5) # Default if missing
#             if not (0.0 <= threshold <= 1.0):
#                 print(f"Warning: Invalid threshold '{threshold_str}'. Using default 0.5")
#                 threshold = 0.5
#         except (ValueError, TypeError):
#             print(f"Warning: Invalid threshold format '{threshold_str}'. Using default 0.5")
#             threshold = 0.5
#         print(f"Using threshold: {threshold:.2f}")

#         # --- Process Resume (Base64 -> Temp File) ---
#         print("Processing resume data...")
#         # Strip data URI scheme (e.g., data:application/pdf;base64,)
#         if resume_b64.startswith('data:'):
#             try:
#                 resume_b64 = resume_b64.split(",", 1)[1]
#             except IndexError:
#                 print("Error: Malformed base64 data URI.")
#                 return create_response(400, {"error": "Malformed base64 data URI"})

#         # Decode base64
#         try:
#             resume_bytes = base64.b64decode(resume_b64)
#             print(f"Resume decoded: {len(resume_bytes)} bytes.")
#         except (base64.binascii.Error, ValueError) as e:
#             print(f"Error: Invalid base64 data in resume: {e}")
#             return create_response(400, {"error": f"Invalid resume base64 data: {e}"})

#         # --- Save to Temp File using context manager ---
#         # Vercel provides a writable /tmp directory
#         print("Saving resume to temporary file...")
#         temp_file_path = None
#         try:
#             # Use delete=False initially, manually delete in finally block for clarity
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir="/tmp") as tmp:
#                 tmp.write(resume_bytes)
#                 temp_file_path = tmp.name # Get the path
#             print(f"Resume saved to: {temp_file_path}")

#             # --- Run Matching ---
#             print(f"Finding matching jobs with threshold {threshold:.2f}...")
#             matching_start_time = time.time()
#             matches_df = current_matcher.find_matching_jobs(temp_file_path, threshold)
#             print(f"Matching completed in {time.time() - matching_start_time:.2f} seconds.")

#             # --- Format Response ---
#             matches_list = matches_df.to_dict(orient="records")
#             # Ensure similarity is float for JSON
#             for match in matches_list:
#                 match["similarity"] = float(match["similarity"])

#             print(f"Returning {len(matches_list)} matching jobs.")
#             total_request_time = time.time() - request_start_time
#             print(f"--- Request ID {request_id} handled successfully in {total_request_time:.2f} seconds ---")
#             return create_response(200, matches_list)

#         finally:
#             # --- Clean up Temp File ---
#             if temp_file_path and os.path.exists(temp_file_path):
#                 try:
#                     os.remove(temp_file_path)
#                     print(f"Temporary file deleted: {temp_file_path}")
#                 except OSError as e:
#                     print(f"Warning: Could not delete temporary file {temp_file_path}: {e}")

#     # --- Catch ALL Other Exceptions ---
#     except RuntimeError as e: # Catch initialization errors specifically
#          print(f"RUNTIME ERROR (likely initialization): {e}")
#          # Avoid leaking detailed internal errors unless debugging
#          return create_response(500, {
#              "error": "Server initialization failed. Please try again later or contact support.",
#              # "details": str(e) # Only for debugging
#          })
#     except FileNotFoundError as e:
#          print(f"FILE NOT FOUND ERROR: {e}")
#          print(traceback.format_exc())
#          return create_response(500, {
#              "error": "Server configuration error: A required data file could not be found.",
#              # "details": str(e) # Only for debugging
#          })
#     except Exception as e:
#         error_details = traceback.format_exc()
#         print(f"--- UNEXPECTED ERROR processing request ID {request_id} ---")
#         print(error_details)
#         # Return a generic error message to the client
#         return create_response(500, {
#             "error": "An unexpected internal server error occurred while processing your request.",
#             # "details": str(e) # Consider logging this instead of returning
#         })

# # Vercel entry point for Python serverless functions
# # Usually expects a handler function, common practice to name it 'handler'
# # but the file name (`match.py`) determines the route `/api/match`
# # This `default` might be used by some Vercel runtimes, keep it simple:
# # def default(request):
# #     return handler(request)
# # However, often just defining handler is enough if Vercel calls it directly.
# # If deployed and /api/match doesn't work, try renaming handler to 'api'
# # or check Vercel Python runtime documentation. Assuming 'handler' is standard.