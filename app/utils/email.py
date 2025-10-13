"""
Email utility for sending notifications to users
Uses Brevo API (not SMTP) for cloud platform compatibility
"""
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Brevo API"""
    
    def __init__(self):
        self.brevo_api_key = getattr(settings, 'BREVO_API_KEY', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', None)
        self.from_name = getattr(settings, 'FROM_NAME', 'Leadership Development')
        
        # Configure Brevo API
        if self.brevo_api_key:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.brevo_api_key
            self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
        else:
            self.api_instance = None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via Brevo API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if Brevo API is configured
            if not self.brevo_api_key or not self.from_email:
                logger.warning("Brevo API not configured. Email not sent.")
                logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
                return True  # Return True for development/testing
            
            # Prepare email data
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"email": self.from_email, "name": self.from_name},
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Send via Brevo API
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"✅ Email sent successfully to {to_email} (Message ID: {api_response.message_id})")
            return True
            
        except ApiException as e:
            logger.error(f"❌ Brevo API error sending to {to_email}: {e}")
            logger.error(f"Status code: {e.status}, Reason: {e.reason}")
            logger.error(f"Response body: {e.body}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            logger.exception("Full error traceback:")
            return False


def send_lesson_reminder(
    user_email: str,
    user_name: str,
    available_lessons: int,
    is_followup: bool = False,
    reminder_type: str = "1"
) -> bool:
    """
    Send lesson reminder email to user
    
    Args:
        user_email: User's email address
        user_name: User's name
        available_lessons: Number of available lessons
        is_followup: Whether this is a follow-up reminder
        reminder_type: Type of reminder (1 or 2)
    
    Returns:
        bool: True if sent successfully
    """
    email_service = EmailService()
    
    # Determine subject and content based on reminder type
    if is_followup:
        subject = "Reminder: Don't Miss Your Leadership Lesson!"
        greeting = f"Hi {user_name},"
        message_body = f"""
        <p>This is a friendly follow-up reminder that you have <strong>{available_lessons}</strong> 
        lesson{"s" if available_lessons > 1 else ""} waiting for you!</p>
        <p>Take a few minutes to complete your leadership development journey today.</p>
        """
    else:
        subject = "Your Leadership Lesson is Ready!"
        greeting = f"Hello {user_name},"
        message_body = f"""
        <p>You have <strong>{available_lessons}</strong> new lesson{"s" if available_lessons > 1 else ""} 
        available to complete!</p>
        <p>Continue your leadership development journey by completing your lesson today.</p>
        """
    
    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #666;
                font-size: 12px;
            }}
            .stats {{
                background: white;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #667eea;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Leadership Development</h1>
        </div>
        <div class="content">
            <p>{greeting}</p>
            {message_body}
            
            <div class="stats">
                <strong>Available Lessons:</strong> {available_lessons}<br>
                <strong>Status:</strong> {"Follow-up Reminder" if is_followup else "New Lesson Available"}
            </div>
            
            <p>
                <a href="{settings.APP_URL}" class="button">
                    Complete Your Lesson Now
                </a>
            </p>
            
            <p>Keep up the great work on your leadership journey!</p>
            
            <p>
                Best regards,<br>
                <strong>Leadership Development Team</strong>
            </p>
        </div>
        <div class="footer">
            <p>You are receiving this email because you have enabled lesson reminders.</p>
            <p>To update your preferences, visit your account settings.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    {greeting}
    
    {"This is a follow-up reminder!" if is_followup else "Your lesson is ready!"}
    
    You have {available_lessons} lesson{"s" if available_lessons > 1 else ""} available to complete.
    
    Visit {settings.APP_URL} to continue your leadership development journey.
    
    Best regards,
    Leadership Development Team
    
    ---
    You are receiving this email because you have enabled lesson reminders.
    To update your preferences, visit your account settings.
    """
    
    return email_service.send_email(
        to_email=user_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

