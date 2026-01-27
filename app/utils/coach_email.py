"""
Email utility for coach sending custom emails to participants
"""
import logging
from app.utils.email import EmailService
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_coach_custom_email(
    recipient_email: str,
    recipient_name: str,
    subject: str,
    message_body: str,
    coach_name: str = "Your Coach"
) -> bool:
    """
    Send custom email from coach to participant
    
    Args:
        recipient_email: Participant's email address
        recipient_name: Participant's name
        subject: Email subject (provided by coach)
        message_body: Email body content (provided by coach, can be HTML or plain text)
        coach_name: Coach's name
    
    Returns:
        bool: True if sent successfully
    """
    email_service = EmailService()
    
    # Check if message contains HTML tags
    is_html = '<' in message_body and '>' in message_body
    
    if is_html:
        # Use coach's HTML directly but wrap it in a basic template
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
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Message from Your Coach</h1>
            </div>
            <div class="content">
                <p>Hello {recipient_name},</p>
                {message_body}
                <p>
                    Best regards,<br>
                    <strong>{coach_name}</strong>
                </p>
            </div>
            <div class="footer">
                <p>This email was sent by your coach through the {settings.PROJECT_NAME}.</p>
            </div>
        </body>
        </html>
        """
    else:
        # Convert plain text to HTML
        # Replace line breaks with <br> and paragraphs with <p>
        formatted_message = message_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
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
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Message from Your Coach</h1>
            </div>
            <div class="content">
                <p>Hello {recipient_name},</p>
                <p>{formatted_message}</p>
                <p>
                    Best regards,<br>
                    <strong>{coach_name}</strong>
                </p>
            </div>
            <div class="footer">
                <p>This email was sent by your coach through the {settings.PROJECT_NAME}.</p>
            </div>
        </body>
        </html>
        """
    
    # Plain text version
    text_content = f"""
    Hello {recipient_name},
    
    {message_body}
    
    Best regards,
    {coach_name}
    
    ---
    This email was sent by your coach through the {settings.PROJECT_NAME}.
    """
    
    return email_service.send_email(
        to_email=recipient_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

