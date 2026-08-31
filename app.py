import sys
from flask import Flask, jsonify, render_template
from src.config import get_config
from src.logging_config import logger
from src.api.routes import api_bp

def create_app():
    config = get_config()
    logger.info(f"Initializing JeevaAi MedeBot (Environment: {config.APP_ENV})")

    # Verify PDF configuration
    pdf_path = config.get_absolute_pdf_path()
    if not config.validate_pdf_exists():
        logger.error(f"Configured PDF source file not found at: {pdf_path}")
    else:
        logger.info(f"PDF source verified: {pdf_path}")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["APP_CONFIG"] = config

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/", methods=["GET"])
    def root():
        """Serves the primary web application interface."""
        return render_template("index.html")

    return app

if __name__ == "__main__":
    config = get_config()
    app = create_app()
    logger.info(f"Starting server on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
