import sqlite3
from backend.config import Config
from backend.logger import logger

def get_db_connection():
    """Create and return a new SQLite database connection."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schemas if tables do not exist."""
    Config.validate()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device TEXT NOT NULL,
                status TEXT NOT NULL,
                battery TEXT,
                timestamp TEXT NOT NULL,
                ip_address TEXT
            )
        """)
        conn.commit()
        logger.info(f"Database schema initialized successfully at {Config.DATABASE_PATH}")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize SQLite database: {e}")
        raise
    finally:
        if conn:
            conn.close()
