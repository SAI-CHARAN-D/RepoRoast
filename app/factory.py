
import os
from flask import Flask
from dotenv import load_dotenv
from app.services.guardrail_service import ensure_cache_dir
from app.services.tts_service import ensure_generated_dir

load_dotenv()


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure cache and generated dirs exist
    ensure_cache_dir()
    ensure_generated_dir()
    
    # Register Blueprints
    from app import routes
    app.register_blueprint(routes.bp)

    return app
