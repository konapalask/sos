import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Config:
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Resolve relative paths relative to BASE_DIR
    db_path = os.getenv("DATABASE_PATH", "backend/database/sos.db")
    DATABASE_PATH = str(BASE_DIR / db_path) if not Path(db_path).is_absolute() else db_path
    
    log_path = os.getenv("LOG_FILE_PATH", "backend/logs/sos.log")
    LOG_FILE_PATH = str(BASE_DIR / log_path) if not Path(log_path).is_absolute() else log_path
    
    # Parse contacts list
    contacts_str = os.getenv("WHATSAPP_CONTACTS", "919293929292")
    WHATSAPP_CONTACTS = [
        num.strip() for num in contacts_str.split(",") if num.strip()
    ]
    
    SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "false").lower() == "true"
    DEVICE_ID = os.getenv("DEVICE_ID", "SOS001")

    # Chrome User Profile Directory (saves Selenium/WhatsApp cookies)
    CHROME_USER_DATA_DIR = str(BASE_DIR / "backend" / "selenium_session")

    @classmethod
    def validate(cls):
        """Validate configurations and ensure directories exist."""
        try:
            # Ensure log and database directories exist
            Path(cls.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
            Path(cls.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
            Path(cls.CHROME_USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Fallback to /tmp (the only writable directory in Vercel serverless environment)
            print(f"Read-only filesystem detected ({e}). Falling back to /tmp storage.")
            cls.DATABASE_PATH = "/tmp/sos.db"
            cls.LOG_FILE_PATH = "/tmp/sos.log"
            cls.CHROME_USER_DATA_DIR = "/tmp/selenium_session"
            
            # Re-attempt creation in /tmp directory
            Path(cls.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
            Path(cls.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
            Path(cls.CHROME_USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
            
        if not cls.WHATSAPP_CONTACTS:
            print("WARNING: WHATSAPP_CONTACTS is empty. No notifications will be sent.")

