import logging
import sys
from pathlib import Path
from backend.config import Config

def setup_logger():
    """Configure system-wide logging."""
    Config.validate()

    logger = logging.getLogger("sos_system")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if logger initialized multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        try:
            file_handler = logging.FileHandler(Config.LOG_FILE_PATH, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}", file=sys.stderr)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    return logger

# Globally available logger instance
logger = setup_logger()
