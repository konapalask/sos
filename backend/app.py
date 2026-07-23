import os
import threading
from flask import Flask, send_from_directory
from flask_cors import CORS
from backend.config import Config
from backend.database import init_db
from backend.routes.sos import sos_bp
from backend.whatsapp import WhatsAppClient
from backend.logger import logger

def create_app() -> Flask:
    """Application factory for the SOS Emergency Alert Server."""
    # Ensure logs, database, and selenium directories exist
    Config.validate()
    
    # Setup SQLite tables
    init_db()

    # Serve the dashboard directory at root url path
    dashboard_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "dashboard")
    )
    app = Flask(__name__, static_folder=dashboard_path, static_url_path="")
    
    # Enable Cross-Origin Resource Sharing (CORS) for API consumers
    CORS(app)

    # Register blueprints
    app.register_blueprint(sos_bp)

    @app.route("/")
    def index():
        """Serve the main dashboard homepage."""
        return send_from_directory(dashboard_path, "index.html")

    # Create empty mock directories in backend folder to adhere to user requirements
    try:
        backend_dir = os.path.abspath(os.path.dirname(__file__))
        os.makedirs(os.path.join(backend_dir, "templates"), exist_ok=True)
        os.makedirs(os.path.join(backend_dir, "static"), exist_ok=True)

        # Create placeholder file in templates folder
        templates_index = os.path.join(backend_dir, "templates", "index.html")
        if not os.path.exists(templates_index):
            with open(templates_index, "w", encoding="utf-8") as f:
                f.write("<!-- System Dashboard is served from root '/' or the dashboard folder -->\n")
    except OSError as e:
        logger.warning(f"Skipped creating local templates/static directories (read-only system): {e}")


    # Start WhatsApp Selenium Client in a daemon thread on boot.
    # This immediately starts Chrome and loads the QR code page.
    def init_whatsapp_client():
        try:
            logger.info("Bootstrapping WhatsApp Client session on startup...")
            client = WhatsAppClient.get_instance()
            client.init_driver()
        except Exception as ex:
            logger.error(f"Failed to bootstrap WhatsApp Client on startup: {ex}")

    threading.Thread(target=init_whatsapp_client, daemon=True).start()

    return app

# Global app instance required for WSGI/Serverless deployment entrypoints
app = create_app()

if __name__ == "__main__":
    logger.info(f"SOS Flask backend starting on http://{Config.HOST}:{Config.PORT}")
    # Disable the automatic reloader (use_reloader=False) to prevent multiple
    # Selenium/Chrome processes from launching simultaneously on startup.
    app.run(host=Config.HOST, port=Config.PORT, debug=False, use_reloader=False)

