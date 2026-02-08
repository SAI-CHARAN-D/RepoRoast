
import re

def generate_tree(files):
    """
    Generates a tree-like string representation of the repository structure.
    """
    tree_str = "Repository Structure:\n"
    sorted_paths = sorted([f['path'] for f in files])
    
    # Simple list approach for now, a full tree ASCII art is nice but complex to get perfect
    # Let's do an indented list which is token-efficient and clear
    for path in sorted_paths:
        tree_str += f"- {path}\n"
        
    return tree_str

def extract_interface(content, language):
    """
    Extracts high-level structure (imports, classes, functions) from code based on language.
    Returns a string summary.
    """
    lines = content.splitlines()
    summary = []
    
    # Regex patterns for different languages
    patterns = {
        'Python': [
            r'^(import|from)\s+', 
            r'^class\s+\w+', 
            r'^def\s+\w+', 
            r'^@'
        ],
        'JavaScript': [
            r'^(import|export)\s+', 
            r'^(const|let|var)\s+\w+\s*=\s*require\(', 
            r'^class\s+\w+', 
            r'^function\s+\w+', 
            r'^(const|ket|var)\s+\w+\s*=\s*\(', # Arrow functions (rough)
            r'^\s*\w+\s*\([^)]*\)\s*{' # Method signatures
        ],
        'TypeScript': [
             r'^(import|export)\s+', 
             r'^class\s+\w+', 
             r'^interface\s+\w+', 
             r'^type\s+\w+', 
             r'^function\s+\w+'
        ],
        'Java': [
            r'^package\s+', 
            r'^import\s+', 
            r'^\s*public\s+(class|interface|enum)\s+', 
            r'^\s*public\s+\w+\s+\w+\(' # public methods
        ],
        'Go': [
            r'^package\s+', 
            r'^import\s+', 
            r'^func\s+'
        ]
    }
    
    lang_patterns = patterns.get(language, [])
    if not lang_patterns:
        # Fallback: First 20 lines
        return "\n".join(lines[:20]) + "\n... (content omitted)"
        
    for line in lines:
        line_strip = line.strip()
        # Keep empty lines for readability? Maybe compact it.
        if not line_strip:
            continue
            
        # Check against patterns
        # We use the original line to preserve indentation for Python/YAML
        if any(re.search(p, line) for p in lang_patterns):
            summary.append(line)
            
    summary.append(f"... (Implementation details omitted for {language} file)")
    return "\n".join(summary)

def generate_blueprint(repo_structure):
    """
    Generates the single prompt context string.
    """
    files = repo_structure['files']
    
    # 1. Tree Structure
    blueprint = "=== REPOSITORY BLUEPRINT ===\n\n"
    blueprint += generate_tree(files)
    blueprint += "\n" + "="*30 + "\n\n"
    
    # 2. File Contents
    for file in files:
        category = file.get('category', 'INTERFACE_ONLY') # Default to interface
        path = file['path']
        language = file.get('language', 'Unknown')
        content = file.get('content', '')
        
        if category == 'IGNORE':
            continue
            
        blueprint += f"=== FILE: {path} ({language}) ===\n"
        blueprint += f"Category: {category}\n"
        
        if category == 'FULL_CODE':
            blueprint += content
        else:
            # INTERFACE_ONLY
            blueprint += extract_interface(content, language)
            
        blueprint += "\n=== END FILE ===\n\n"
        
    return blueprint

if __name__ == "__main__":
    # Mock data validation
    mock_files = [
        {
            'path': 'src/main.py', 
            'language': 'Python',
            'category': 'FULL_CODE',
            'content': 'import os\n\ndef main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()'
        },
        {
            'path': 'src/utils.py', 
            'language': 'Python',
            'category': 'INTERFACE_ONLY',
            'content': 'import math\n\ndef fast_inv_sqrt(x):\n    # Magic number\n    scan_lines_logic_here()\n    return 1/x\n\nclass MathHelper:\n    def __init__(self):\n        pass\n    def help(self):\n        return True'
        },
        {
             'path': 'tests/test_foo.py',
             'category': 'IGNORE',
             'content': 'def test_foo(): assert True'
        }
    ]
    
    structure = {'files': mock_files}
    print(generate_blueprint(structure))
