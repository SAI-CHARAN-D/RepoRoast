
import os
import shutil
from app.services.github_service import ingest_repo

def test_ingest():
    print("Testing Git Ingestion...")
    # Use a small, public, stable repo
    test_url = "https://github.com/octocat/Hello-World"
    try:
        result = ingest_repo(test_url)
        print(f"Ingestion Success!")
        print(f"Files found: {len(result['files'])}")
        print(f"Commit: {result['meta']['commit_hash']}")
    except Exception as e:
        print(f"Ingestion Failed: {e}")
        # Check if git is in path
        if shutil.which("git") is None:
            print("CRITICAL: 'git' executable not found in PATH.")

if __name__ == "__main__":
    test_ingest()
