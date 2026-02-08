
import os
import re

class FileCategory:
    IGNORE = "IGNORE"
    INTERFACE_ONLY = "INTERFACE_ONLY"
    FULL_CODE = "FULL_CODE"

# Regex patterns for deterministic classification

# 1. IGNORE: Tests, Mocks, Generated, Assets
IGNORE_PATTERNS = [
    r'test', r'spec', r'mock', r'e2e', r'fixture',
    r'node_modules', r'venv', r'env', r'dist', r'build', r'target',
    r'assets?', r'images?', r'icons?', r'styles?', r'\.css$', r'\.scss$', r'\.svg$',
    r'\.min\.js$', r'\.map$', r'package-lock\.json$', r'yarn\.lock$',
    r'migrations?', r'seeds?', r'factories?',
    r'__pycache__', r'\.pyc$', r'\.DS_Store$', r'Thumbs\.db$'
]

# 2. INTERFACE_ONLY: Utils, Helpers, Libs, Config, Types
INTERFACE_PATTERNS = [
    r'utils?', r'helpers?', r'common', r'shared',
    r'lib', r'constants?', r'types?', r'interfaces?', r'dtos?',
    r'models?', r'schemas?', r'entities?',
    r'config', r'settings', r'environments?',
    r'middleware', r'interceptors?', r'filters?',
    r'hooks?', r'providers?'
]

# 3. FULL_CODE Candidates: Entry Points, Core, Orchestration
# Note: These are patterns that *boost* the chance of being FULL_CODE
FULL_CODE_BOOST_PATTERNS = [
    r'main\.', r'app\.', r'index\.', r'server\.', r'run\.',
    r'routes?', r'controllers?', r'views?', r'handlers?',
    r'api', r'core', r'services?', r'logic',
    r'wsgi\.', r'asgi\.', r'manage\.py',
    r'Dockerfile', r'docker-compose'
]

def classify_file(repo_structure):
    """
    Annotates each file in the repo structure with a category.
    Mutates repo_structure in place.
    """
    files = repo_structure['files']
    
    # We now trust Gemini's massive context window. 
    # Strategy: 
    # 1. IGNORE irrelevant files (assets, locks, etc.)
    # 2. Everything else is FULL_CODE unless it's huge, then INTERFACE_ONLY.
    
    for file in files:
        path = file['path']
        path_lower = path.lower()
        
        # Step 1: Check IGNORE
        if any(re.search(p, path_lower) for p in IGNORE_PATTERNS):
            file['category'] = FileCategory.IGNORE
            continue

        # Step 2: Check INTERFACE_ONLY (Explicit utility/config types that provide little roasted value)
        # We can relax this too. Let's only downgrade if it matches specific low-value patterns.
        # actually, for a good roast, we want to see the utils too.
        # Let's only force INTERFACE_ONLY if it's a "definition" file or generated.
        if path_lower.endswith('.d.ts') or path_lower.endswith('.min.js'):
            file['category'] = FileCategory.INTERFACE_ONLY
            continue
            
        # Step 3: Default to FULL_CODE
        # We rely on GuardrailService to prune if the TOTAL request gets too big.
        # But here, we categorize as much as possible as FULL_CODE.
        file['category'] = FileCategory.FULL_CODE

    return repo_structure

def get_annotated_files(repo_structure):
    """Returns a list of tuples (path, category) for display/debug."""
    return [(f['path'], f.get('category', 'UNKNOWN')) for f in repo_structure['files']]

if __name__ == "__main__":
    # Mock data for testing
    mock_repo = {
        'files': [
            {'path': 'src/main.py', 'lines': 50},
            {'path': 'src/utils/helper.py', 'lines': 100},
            {'path': 'tests/test_main.py', 'lines': 200},
            {'path': 'README.md', 'lines': 10},
            {'path': 'requirements.txt', 'lines': 5},
            {'path': 'src/api/routes.py', 'lines': 80},
            {'path': 'src/core/logic.py', 'lines': 300},
            {'path': 'src/models/user.py', 'lines': 50},
            {'path': 'config.py', 'lines': 20},
            {'path': 'assets/logo.png', 'lines': 0},
            {'path': 'app.py', 'lines': 40}
        ]
    }
    
    print("Classifying mock repo...")
    classify_file(mock_repo)
    
    for f in mock_repo['files']:
        print(f"{f['category']}: {f['path']}")
