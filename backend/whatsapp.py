import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.config import Config
from backend.logger import logger

class WhatsAppClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Retrieve the Singleton instance of the WhatsAppClient."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.driver = None
        self._is_initializing = False

    def init_driver(self):
        """Initialize the Chrome WebDriver with options and persistent user-data profile."""
        if self.driver:
            try:
                # Test if the driver instance is active
                self.driver.current_url
                return
            except Exception:
                logger.warning("WebDriver session is unresponsive. Re-initializing...")
                self.close()

        if self._is_initializing:
            return

        self._is_initializing = True
        logger.info("Initializing Selenium Chrome WebDriver...")
        try:
            options = webdriver.ChromeOptions()
            options.add_argument(f"user-data-dir={Config.CHROME_USER_DATA_DIR}")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Exclude automation indicators to prevent blocking by WhatsApp
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            if Config.SELENIUM_HEADLESS:
                options.add_argument("--headless=new")
                # Standard User Agent when running headless to avoid blocking
                options.add_argument(
                    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )

            # Initialize Chrome
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(45)
            logger.info("Chrome WebDriver running. Opening WhatsApp Web...")
            
            # Start page load in background
            self.driver.get("https://web.whatsapp.com")
        except Exception as e:
            logger.error(f"WebDriver initialization failed: {e}")
            self.driver = None
            raise e
        finally:
            self._is_initializing = False

    def check_login_status(self) -> str:
        """
        Check if user is logged into WhatsApp Web.
        Returns:
            "logged_in"  - Main WhatsApp UI is visible.
            "waiting_for_qr" - QR code is visible.
            "loading"    - Page is loading or state is unknown.
            "disconnected" - WebDriver is not running.
        """
        if not self.driver:
            return "disconnected"
        
        try:
            # Check for the chat list (pane-side) or the search bar data-tab
            chat_pane = self.driver.find_elements(
                By.XPATH, "//div[@id='pane-side'] | //div[@contenteditable='true'][@data-tab='3']"
            )
            if chat_pane:
                return "logged_in"
            
            # Check for the QR code canvas/element
            qr_canvas = self.driver.find_elements(By.XPATH, "//canvas | //div[@data-ref]")
            if qr_canvas:
                return "waiting_for_qr"

            return "loading"
        except Exception as e:
            logger.warning(f"Error checking login status: {e}")
            return "disconnected"

    def send_message(self, phone_number: str, message_text: str) -> bool:
        """
        Send a WhatsApp message to a given phone number.
        Pre-populates message in text field via standard URL format, then clicks send.
        """
        try:
            self.init_driver()
        except Exception as e:
            logger.error(f"Cannot send message because WebDriver failed to start: {e}")
            return False

        # Parse number to digits only
        clean_phone = "".join(filter(str.isdigit, phone_number))
        if not clean_phone:
            logger.error(f"Invalid phone number provided: {phone_number}")
            return False

        encoded_message = urllib.parse.quote(message_text)
        url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
        
        logger.info(f"Navigating to: https://web.whatsapp.com/send?phone={clean_phone}")
        try:
            self.driver.get(url)
            
            # Wait for text area container to confirm page loading
            wait = WebDriverWait(self.driver, 30)
            text_box_xpath = "//div[@contenteditable='true'][@data-tab='10']"
            text_box = wait.until(EC.presence_of_element_located((By.XPATH, text_box_xpath)))
            
            # Wait a few seconds for send button elements to process
            time.sleep(3)

            # Locate the send button. 
            # In WhatsApp Web, the send button is typically a button element wraps standard send icon.
            send_btn_xpath = "//button[span[@data-icon='send']] | //span[@data-icon='send']/.."
            send_buttons = self.driver.find_elements(By.XPATH, send_btn_xpath)
            
            if send_buttons:
                send_buttons[0].click()
                logger.info(f"Successfully clicked WhatsApp send button for {clean_phone}")
            else:
                # Fallback: send Enter key to the text area input
                text_box.send_keys("\n")
                logger.info(f"Fallback: Sent ENTER key to textbox for {clean_phone}")

            # Sleep to allow message to send over socket connection
            time.sleep(5)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {clean_phone}: {e}")
            # Try to close any dialog boxes (like 'Phone number is invalid' dialog)
            try:
                ok_btn = self.driver.find_elements(
                    By.XPATH, "//div[contains(text(), 'OK')] | //button[contains(span, 'OK')]"
                )
                if ok_btn:
                    ok_btn[0].click()
                    logger.info("Closed phone number error dialog.")
            except Exception:
                pass
            return False

    def close(self):
        """Close the Chrome browser driver session."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error during WebDriver quit: {e}")
            self.driver = None
            logger.info("WebDriver closed.")
