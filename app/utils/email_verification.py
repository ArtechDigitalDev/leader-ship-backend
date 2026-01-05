"""
Email verification utilities - Token generation, validation and sending verification emails
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import logging
from app.core.config import settings
from app.utils.email import EmailService

logger = logging.getLogger(__name__)


# ==================== Token Management ====================

def create_email_verification_token(email: str) -> str:
    """
    Create a JWT token for email verification
    
    Args:
        email: User's email address
    
    Returns:
        str: JWT token
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=24)  # Token valid for 24 hours
    
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "email_verification"
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_email_token(token: str) -> str | None:
    """
    Verify email verification token and extract email
    
    Args:
        token: JWT token
    
    Returns:
        str: Email if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "email_verification":
            return None
        
        return email
    except JWTError:
        return None


# ==================== Email Sending ====================

def send_verification_email(
    user_email: str,
    user_name: str,
    verification_token: str
) -> bool:
    """
    Send email verification link to user
    
    Args:
        user_email: User's email address
        user_name: User's name
        verification_token: JWT verification token
    
    Returns:
        bool: True if sent successfully
    """
    email_service = EmailService()
    
    # Create verification link
    verification_link = f"{settings.APP_URL}/verify-email?token={verification_token}"
    
    subject = "Verify Your Email - Intent2Lead"
    
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
            .warning {{
                background: #fff3cd;
                padding: 15px;
                border-left: 4px solid #ffc107;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✉️ Verify Your Email</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            
            <p>Thank you for signing up for Intent2Lead!</p>
            
            <p>To complete your registration and start your leadership journey, please verify your email address by clicking the button below:</p>
            
            <p style="text-align: center;">
                <a href="{verification_link}" class="button">
                    Verify Email Address
                </a>
            </p>
            
            <div class="warning">
                <strong>Note:</strong> This verification link will expire in 24 hours.
            </div>
            
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{verification_link}</p>
            
            <p>If you didn't create an account, you can safely ignore this email.</p>
            
            <p>
                Best regards,<br>
                <strong>Intent2Lead Team</strong>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Hello {user_name},
    
    Thank you for signing up for Intent2Lead!
    
    To complete your registration, please verify your email address by clicking the link below:
    
    {verification_link}
    
    Note: This verification link will expire in 24 hours.
    
    If you didn't create an account, you can safely ignore this email.
    
    Best regards,
    Intent2Lead Team
    
    ---
    This is an automated email. Please do not reply to this message.
    """
    
    return email_service.send_email(
        to_email=user_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )
