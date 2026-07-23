import threading
from flask import Blueprint, request, jsonify
from backend.services.database_service import DatabaseService
from backend.services.notification import NotificationService
from backend.services.wifi import WifiService
from backend.whatsapp import WhatsAppClient
from backend.logger import logger

sos_bp = Blueprint("sos", __name__)

@sos_bp.route("/sos", methods=["POST"])
def trigger_sos():
    """
    Endpoint for ESP32 and mock clients to trigger alerts.
    Saves the event to SQLite, fires WhatsApp alerts in a background thread,
    and returns immediately to keep request durations minimal.
    """
    try:
        # Retrieve JSON body safely
        data = request.get_json(silent=True) or {}
        
        # Extract properties with default fallbacks
        device = data.get("device", "UnknownDevice")
        status = data.get("status", "Emergency")
        battery = data.get("battery", "100")
        timestamp = data.get("timestamp", "auto")
        ip_address = request.remote_addr or "127.0.0.1"

        logger.info(
            f"API POST /sos: Received alert from {device} (IP: {ip_address}) with battery: {battery}%"
        )

        # 1. Insert alert in database
        saved_record = DatabaseService.save_alert(
            device=device,
            status=status,
            battery=battery,
            ip_address=ip_address,
            timestamp_val=timestamp
        )

        # 2. Dispatch notifications asynchronously using a daemon thread
        # This allows Flask to return response immediately to the ESP32
        actual_time = saved_record["timestamp"]
        notify_thread = threading.Thread(
            target=NotificationService.send_sos_alerts,
            args=(device, battery, actual_time),
            daemon=True
        )
        notify_thread.start()

        return jsonify({
            "status": "success",
            "message": "SOS registered. WhatsApp notifications triggered in background.",
            "data": saved_record
        }), 201

    except Exception as e:
        logger.error(f"Failed to process /sos request: {e}")
        return jsonify({
            "status": "error",
            "message": f"Server failed to register alert: {str(e)}"
        }), 500

@sos_bp.route("/alerts", methods=["GET"])
def get_alerts():
    """
    Endpoint to retrieve logged alerts.
    Supports filter query parameters.
    """
    search_val = request.args.get("search", "")
    try:
        alerts = DatabaseService.get_alerts(search_query=search_val)
        return jsonify(alerts), 200
    except Exception as e:
        logger.error(f"Failed to retrieve alerts list: {e}")
        return jsonify([]), 500

@sos_bp.route("/status", methods=["GET"])
def get_status():
    """
    Endpoint to get current server statuses.
    Includes active Internet verification, SQLite analytics, and WhatsApp Web state.
    """
    try:
        whatsapp_state = WhatsAppClient.get_instance().check_login_status()
        net_connected = WifiService.is_connected()
        total_count = DatabaseService.get_total_count()
        today_count = DatabaseService.get_today_count()

        return jsonify({
            "status": "active",
            "internet_connected": net_connected,
            "whatsapp_status": whatsapp_state,
            "metrics": {
                "total_alerts": total_count,
                "today_alerts": today_count
            }
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch statuses: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
