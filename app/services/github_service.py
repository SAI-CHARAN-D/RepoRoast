
import os
import shutil
import tempfile
import uuid
from git import Repo
import mimetypes

# Constants for filtering
EXCLUDED_DIRS = {
    '.git', 'node_modules', 'venv', 'env', '.venv', 'dist', 'build', 
    '__pycache__', 'target', 'bin', 'obj', '.idea', '.vscode'
}

EXCLUDED_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.mp4', '.mp3', 
    '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.dylib', 
    '.pyc', '.class', '.o', '.lock'
}

MAX_FILE_SIZE_BYTES = 1000 * 1024  # 1MB limit per file

def detect_language(file_path):
    """Simple extension-based language detection."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    mapping = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.html': 'HTML',
        '.css': 'CSS',
        '.sql': 'SQL',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.xml': 'XML',
        '.sh': 'Shell',
        '.bat': 'Batch'
    }
    return mapping.get(ext, 'Unknown')

def is_text_file(file_path):
    """Check if a file is text or binary using mimetypes and content inspection."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and not mime_type.startswith('text'):
        return False
    
    # Fallback: Check for null bytes in the first 1024 bytes
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return False
    except Exception:
        return False
        
    return True

def ingest_repo(repo_url):
    """
    Clones a repo, filters files, and returns a structured representation.
    """
    temp_dir = tempfile.mkdtemp()
    repo_path = os.path.join(temp_dir, str(uuid.uuid4()))
    
    try:
        # Clone the repository
        Repo.clone_from(repo_url, repo_path, depth=1)
        
        commit_hash = Repo(repo_path).head.commit.hexsha
        default_branch = Repo(repo_path).active_branch.name
    
        repo_structure = {
            'url': repo_url,
            'files': [],
            'meta': {
                'commit_hash': commit_hash,
                'default_branch': default_branch
            },
            'stats': {
                'total_lines': 0,
                'file_count': 0,
                'languages': {}
            }
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in EXCLUDED_EXTENSIONS:
                    continue
                
                if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
                    continue
                
                if not is_text_file(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        line_count = len(content.splitlines())
                        
                        language = detect_language(file_path)
                        
                        repo_structure['files'].append({
                            'path': rel_path,
                            'content': content,
                            'lines': line_count,
                            'language': language
                        })
                        
                        # Update stats
                        repo_structure['stats']['total_lines'] += line_count
                        repo_structure['stats']['file_count'] += 1
                        repo_structure['stats']['languages'][language] = \
                            repo_structure['stats']['languages'].get(language, 0) + 1
                            
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
                    continue

        return repo_structure
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            def on_rm_error(func, path, exc_info):
                import stat
                # Change the file attribute to allow deletion
                os.chmod(path, stat.S_IWRITE)
                try:
                    func(path)
                except Exception:
                    pass
            
            shutil.rmtree(temp_dir, onerror=on_rm_error)

if __name__ == "__main__":
    # Test with a sample repo (e.g., this one or a popular one)
    test_url = "https://github.com/pallets/flask" # Example
    print(f"Ingesting {test_url}...")
    result = ingest_repo(test_url)
    print(f"Total Files: {result['stats']['file_count']}")
    print(f"Total Lines: {result['stats']['total_lines']}")
    print("Languages:", result['stats']['languages'])
