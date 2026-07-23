import datetime
from backend.config import Config
from backend.whatsapp import WhatsAppClient
from backend.logger import logger

class NotificationService:
    @staticmethod
    def send_sos_alerts(device_id: str, battery: str, alert_time: str = None) -> bool:
        """
        Send SOS messages sequentially to all configured contacts.
        Runs on a background thread to prevent blocking HTTP endpoints.
        """
        if not alert_time or alert_time.lower() == "auto":
            alert_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Structure the message payload as requested
        message = (
            "🚨 SOS ALERT 🚨\n\n"
            "Emergency Button Pressed\n\n"
            f"Device: {device_id}\n\n"
            f"Time: {alert_time}\n\n"
            f"Battery: {battery}%\n\n"
            "Please contact immediately."
        )

        contacts = Config.WHATSAPP_CONTACTS
        if not contacts:
            logger.warning("Notification Service: No phone numbers found in config. Exiting.")
            return False

        logger.info(f"Notification Service: Preparing to dispatch alerts to {len(contacts)} contacts.")
        client = WhatsAppClient.get_instance()
        
        success_count = 0
        for contact in contacts:
            logger.info(f"Notification Service: Dispatching alert to {contact}...")
            success = client.send_message(contact, message)
            if success:
                success_count += 1
                logger.info(f"Notification Service: Alert successfully sent to {contact}")
            else:
                logger.error(f"Notification Service: Failed sending alert to {contact}")
                
        logger.info(
            f"Notification Service: Alerts batch finished. Sent {success_count} of {len(contacts)} messages."
        )
        return success_count > 0
