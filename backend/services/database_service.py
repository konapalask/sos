import datetime
from backend.database import get_db_connection
from backend.logger import logger

class DatabaseService:
    @staticmethod
    def save_alert(device, status, battery, ip_address, timestamp_val=None):
        """Save a new emergency alert in SQLite."""
        # Handle automatic timestamp generation
        if not timestamp_val or timestamp_val.lower() == "auto":
            timestamp_val = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alerts (device, status, battery, timestamp, ip_address) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (device, status, battery, timestamp_val, ip_address)
            )
            conn.commit()
            alert_id = cursor.lastrowid
            logger.info(f"DB Log: Saved Alert ID: {alert_id} for device {device}")
            return {
                "id": alert_id,
                "device": device,
                "status": status,
                "battery": battery,
                "timestamp": timestamp_val,
                "ip_address": ip_address
            }
        except Exception as e:
            logger.error(f"Database insertion failed: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_alerts(search_query=None):
        """Fetch all alerts, optionally filtered by a text search query."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            if search_query:
                # Search in device name, status, IP address, or timestamp
                wildcard = f"%{search_query}%"
                cursor.execute(
                    """
                    SELECT * FROM alerts 
                    WHERE device LIKE ? OR status LIKE ? OR ip_address LIKE ? OR timestamp LIKE ?
                    ORDER BY id DESC
                    """,
                    (wildcard, wildcard, wildcard, wildcard)
                )
            else:
                cursor.execute("SELECT * FROM alerts ORDER BY id DESC")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database select failed: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_total_count():
        """Retrieve total alerts count."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM alerts")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Database count query failed: {e}")
            return 0
        finally:
            conn.close()

    @staticmethod
    def get_today_count():
        """Retrieve counts for alerts registered today."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            today_date = datetime.datetime.now().strftime("%Y-%m-%d") + "%"
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp LIKE ?", (today_date,))
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Database count-today query failed: {e}")
            return 0
        finally:
            conn.close()
