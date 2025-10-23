"""
SMS service using Twilio for sending text messages.
"""
from twilio.rest import Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for sending text messages via Twilio."""
    
    def __init__(self):
        """Initialize SMS service with Twilio credentials."""
        self.client = None
        self.from_number = settings.TWILIO_PHONE_NUMBER
        
        # Initialize Twilio client if credentials are available
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                logger.info("SMS service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SMS service: {str(e)}")
                self.client = None
        else:
            logger.warning("SMS service not configured - missing Twilio credentials")
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for Twilio (ensure it starts with +)
        
        Args:
            phone_number: Raw phone number
            
        Returns:
            str: Formatted phone number with country code
        """
        # Remove any spaces, dashes, or parentheses
        cleaned = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # If it doesn't start with +, assume it's a local number and add +1 (US)
        if not cleaned.startswith("+"):
            # For Bangladesh numbers, add +880
            if cleaned.startswith("01") and len(cleaned) == 11:
                cleaned = "+880" + cleaned[1:]  # Remove leading 0, add +880
            else:
                # For other numbers, add +1 (US/Canada)
                cleaned = "+1" + cleaned
        
        return cleaned

    async def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS message to a phone number.
        
        Args:
            to_number: Recipient phone number (e.g., "+1234567890" or "01234567890")
            message: SMS message content
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("SMS service not available - Twilio not configured")
            return False
            
        if not to_number:
            logger.warning("Cannot send SMS - no phone number provided")
            return False
        
        # Format the phone number
        formatted_number = self._format_phone_number(to_number)
        logger.info(f"Formatted phone number: {to_number} -> {formatted_number}")
            
        try:
            # Send SMS via Twilio
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=formatted_number
            )
            
            logger.info(f"SMS sent successfully to {formatted_number} (SID: {message_obj.sid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {formatted_number}: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """Check if SMS service is available and configured."""
        return self.client is not None


# Global SMS service instance
sms_service = SMSService()
