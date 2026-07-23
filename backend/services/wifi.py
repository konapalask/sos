import socket
from backend.logger import logger

class WifiService:
    @staticmethod
    def is_connected() -> bool:
        """
        Verify if the backend server has active network/internet connectivity.
        Attempts a rapid socket connection to Google DNS (8.8.8.8) on port 53.
        """
        try:
            # Short timeout to avoid blocking the main server threads
            socket.setdefaulttimeout(2.0)
            # Create a TCP socket connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("8.8.8.8", 53))
            return True
        except (socket.timeout, socket.error) as e:
            logger.warning(f"Internet connection check failed: {e}")
            return False
