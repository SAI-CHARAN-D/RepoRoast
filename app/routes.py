
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_from_directory
import os
import threading

from app.services.github_service import ingest_repo
from app.services.classifier_service import classify_file
from app.services.blueprint_service import generate_blueprint
from app.services.guardrail_service import (
    Guardrail, get_repo_hash, get_cached_result, save_result, 
    estimate_and_prune, get_repo_data, save_repo_data
)
from app.services.ai_service import AIService
from app.services.tts_service import TTSService

bp = Blueprint('main', __name__)
ai_service = AIService()
tts_service = TTSService()

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/health')
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "reporoast",
        "version": "1.0.0"
    }), 200

@bp.route('/ignite', methods=['POST'])
def ignite():
    data = request.json
    repo_url = data.get('repo_url')
    
    if not repo_url:
        return jsonify({"error": "No URL provided"}), 400
        
    # 1. Processing Lock (Simple demo guard)
    if not Guardrail.acquire_processing_lock():
        return jsonify({"error": "Server busy roasting another victim. Please wait 10 seconds."}), 503
        
    try:
        # 2. Ingest
        print(f"Ingesting {repo_url}...")
        try:
            repo_structure = ingest_repo(repo_url)
        except Exception as e:
            return jsonify({"error": f"Failed to ingest repo: {str(e)}"}), 400

        # 3. Hash & Cache Check
        repo_meta = repo_structure.get('meta', {})
        repo_hash = get_repo_hash(repo_url, repo_meta.get('commit_hash', 'unknown'))
        
        # Save full repo data for code viewer ASAP
        save_repo_data(repo_hash, repo_structure)

        # CACHING DISABLED: Always generate fresh analysis
        # cached_analysis = get_cached_result(repo_hash)
        # if cached_analysis:
        #     print("Cache hit! Serving pre-roasted content.")
        #     return jsonify({"status": "ready", "redirect_url": url_for('main.result', repo_hash=repo_hash)})

        # 4. Classify & Prune
        print("Classifying and pruning...")
        classify_file(repo_structure)
        blueprint = estimate_and_prune(repo_structure)
        
        # 5. AI Analysis
        print("Calling Gemini...")
        analysis = ai_service.analyze_repo(blueprint)
        if "error" in analysis:
             return jsonify(analysis), 500
             
        # 6. Audio Generation
        print("Synthesizing audio...")
        audio_path = tts_service.generate_roast_audio(analysis.get('roast_dialogue', []), repo_hash)
        analysis['audio_path'] = audio_path
        
        # 7. Save Result
        save_result(repo_hash, analysis)
        
        return jsonify({"status": "ready", "redirect_url": url_for('main.result', repo_hash=repo_hash)})

    except Exception as e:
        print(f"Critical error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        Guardrail.release_processing_lock()

@bp.route('/result/<repo_hash>')
def result(repo_hash):
    analysis = get_cached_result(repo_hash)
    if not analysis:
        return redirect(url_for('main.index'))
    
    # Get Repo Name from Metadata
    repo_data = get_repo_data(repo_hash)
    repo_name = f"repo-{repo_hash[:6]}" # Default fallback
    
    if repo_data and 'url' in repo_data:
        url = repo_data['url']
        # Extract "owner/repo" from https://github.com/owner/repo(.git)
        try:
            clean_url = url.rstrip('/')
            if clean_url.endswith('.git'):
                clean_url = clean_url[:-4]
            parts = clean_url.split('/')
            if len(parts) >= 2:
                repo_name = f"{parts[-2]}/{parts[-1]}"
        except Exception:
            pass

    return render_template('result.html', analysis=analysis, repo_hash=repo_hash, repo_name=repo_name)

# --- Code Viewer API ---

@bp.route('/api/repo/<repo_hash>/files')
def get_repo_files(repo_hash):
    repo_data = get_repo_data(repo_hash)
    if not repo_data:
        return jsonify({"error": "Repo not found"}), 404
        
    # Return list of file paths for the tree view
    files = [f['path'] for f in repo_data['files']]
    return jsonify({"files": sorted(files)})

@bp.route('/api/repo/<repo_hash>/file')
def get_file_content(repo_hash):
    path = request.args.get('path')
    repo_data = get_repo_data(repo_hash)
    if not repo_data:
        return jsonify({"error": "Repo not found"}), 404
        
    file_obj = next((f for f in repo_data['files'] if f['path'] == path), None)
    if not file_obj:
         return jsonify({"error": "File not found"}), 404
         
    return jsonify({
        "path": file_obj['path'],
        "content": file_obj.get('content', ''),
        "language": file_obj.get('language', 'text')
    })
    
@bp.route('/generated/<path:filename>')
def serve_generated(filename):
    return send_from_directory('static/generated', filename)
