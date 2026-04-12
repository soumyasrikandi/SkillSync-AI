from flask import Flask, send_from_directory, jsonify
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from app.config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure CORS to allow frontend requests
    CORS(app)

    # Register blueprints
    from app.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Global error handler forcing JSON for all unhandled backend/API exceptions
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        return jsonify({"error": "An unexpected internal server error occurred."}), 500


    # Serve Frontend (Since we use a static index.html with React CDNs)
    # We will point the static folder to the frontend folder
    FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
    
    @app.route('/')
    def serve_index():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        if os.path.exists(os.path.join(FRONTEND_DIR, path)):
            return send_from_directory(FRONTEND_DIR, path)
        return send_from_directory(FRONTEND_DIR, 'index.html')

    return app
