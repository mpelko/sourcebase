"""Flask application initialization and configuration."""

from typing import Any, Optional

from flask import Flask
from flask_cors import CORS


def create_app(config: Optional[dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Enable CORS
    CORS(app)

    # Load default configuration
    app.config.setdefault("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)  # 16MB max file size

    # Apply any custom configuration
    if config:
        app.config.update(config)

    # Register blueprints
    from .routes import chat, documents, search

    app.register_blueprint(documents.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(chat.bp)

    return app
