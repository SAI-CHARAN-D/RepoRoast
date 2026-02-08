
import os
import json
import threading
import hashlib
from app.services.blueprint_service import generate_blueprint

# Constants
CACHE_DIR = os.path.join(os.getcwd(), 'app', 'cache')
SAFE_CHAR_LIMIT = 4000000  # ~1M tokens, leveraging Gemini's large context window
processing_lock = threading.Lock()

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_repo_hash(repo_url, commit_hash):
    """Generates a unique hash for the repo version."""
    raw = f"{repo_url}::{commit_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_cached_result(repo_hash):
    """Returns cached JSON if it exists."""
    ensure_cache_dir()
    cache_path = os.path.join(CACHE_DIR, f"{repo_hash}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_result(repo_hash, result_json):
    """Saves the result to cache."""
    ensure_cache_dir()
    cache_path = os.path.join(CACHE_DIR, f"{repo_hash}.json")
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2)
    except Exception as e:
        print(f"Failed to cache result: {e}")

def get_repo_data(repo_hash):
    """Returns the full cached repository structure (files and content)."""
    ensure_cache_dir()
    cache_path = os.path.join(CACHE_DIR, f"{repo_hash}_repo.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_repo_data(repo_hash, repo_data):
    """Saves the full repo structure to cache (for code viewer)."""
    ensure_cache_dir()
    cache_path = os.path.join(CACHE_DIR, f"{repo_hash}_repo.json")
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(repo_data, f, indent=2)
    except Exception as e:
        print(f"Failed to cache repo data: {e}")

def estimate_and_prune(repo_structure):
    """
    Checks blueprint size. If too large, reduces FULL_CODE files to INTERFACE_ONLY.
    Returns the final blueprint string.
    """
    blueprint = generate_blueprint(repo_structure)
    
    if len(blueprint) <= SAFE_CHAR_LIMIT:
        return blueprint
    
    print(f"Blueprint size {len(blueprint)} exceeds limit {SAFE_CHAR_LIMIT}. Pruning...")
    
    # Pruning Strategy: Downgrade FULL_CODE files to INTERFACE_ONLY, starting from the largest
    # We keep the files sorted by size to prune effectively
    full_code_files = [f for f in repo_structure['files'] if f.get('category') == 'FULL_CODE']
    full_code_files.sort(key=lambda x: len(x.get('content', '')), reverse=True)
    
    for file in full_code_files:
        # Downgrade
        file['category'] = 'INTERFACE_ONLY'
        # Re-generate to check size
        blueprint = generate_blueprint(repo_structure)
        if len(blueprint) <= SAFE_CHAR_LIMIT:
            print(f"Pruned down to {len(blueprint)} chars.")
            return blueprint
            
    # If still too large, return as is (Gemini 1.5 Pro is huge mostly, this is just a latency guard)
    print("Warning: Still exceeds safe limit after pruning all FULL_CODE files.")
    return blueprint

class Guardrail:
    """Singleton-like access to locks and state."""
    @staticmethod
    def acquire_processing_lock():
        return processing_lock.acquire(blocking=False)
    
    @staticmethod
    def release_processing_lock():
        processing_lock.release()

if __name__ == "__main__":
    # Test Stub
    ensure_cache_dir()
    print("Cache dir created at", CACHE_DIR)
