"""
Support Email Utilities

This module contains functions for sending support emails to users who are struggling
with their lessons or have missed multiple lessons.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.utils.email import EmailService

logger = logging.getLogger(__name__)


def create_support_email_content(user_data: Dict[str, Any]) -> tuple[str, str]:
    """
    Create HTML and text content for support emails
    
    Args:
        user_data: User information dictionary
    
    Returns:
        Tuple of (html_content, text_content)
    """
    greeting = f"Hi {user_data['full_name'] or user_data['username']}"
    
    html_content = f"""
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: white; padding: 30px; border: 1px solid #ddd;">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">Leadership Development Support</h2>
            <p style="font-size: 16px; margin-bottom: 20px;">{greeting},</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin: 20px 0;">
                <p style="margin: 0 0 15px 0;">We noticed you might be facing some challenges with your lessons.</p>
                <p style="margin: 0 0 15px 0;"><strong>Are you experiencing any problems?</strong></p>
                <p style="margin: 0 0 15px 0;"><strong>Do you need any help?</strong></p>
                <p style="margin: 0;">We're here to support you on your leadership journey.</p>
            </div>
            
            <p style="margin: 30px 0;">
                <strong>Continue your lessons:</strong><br>
                <a href="https://leadership-development-platform-self.vercel.app" style="color: #3498db; text-decoration: none;">https://leadership-development-platform-self.vercel.app</a>
            </p>
            
            <p style="color: #666; font-size: 14px;">
                Best regards,<br>
                Leadership Development Team
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                This is a support email for your learning progress.<br>
                Reply to this email if you need assistance.
            </p>
        </div>
    </body>
    """
    
    text_content = f"""
    Leadership Development Support
    
    {greeting},
    
    We noticed you might be facing some challenges with your lessons.
    Are you experiencing any problems?
    Do you need any help?
    
    We're here to support you on your leadership journey.
    
    Continue your lessons: https://leadership-development-platform-self.vercel.app
    
    Best regards,
    Leadership Development Team
    
    This is a support email for your learning progress.
    Reply to this email if you need assistance.
    """
    
    return html_content, text_content


def send_support_email_to_struggling_users(db: Session, min_miss_count: int = 3) -> Dict[str, Any]:
    """
    Send support emails to users who have missed lessons
    
    Args:
        db: Database session
        min_miss_count: Minimum number of missed lessons (default: 3)
    
    Returns:
        dict: Results of email sending
    """
    try:
        # Import here to avoid circular imports
        from app.services.scheduler_service import get_users_with_missed_lessons
        
        email_service = EmailService()
        users_with_misses = get_users_with_missed_lessons(db, min_miss_count=min_miss_count)
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        for user_data in users_with_misses:
            try:
                # Create email content
                html_content, text_content = create_support_email_content(user_data)
                
                # Send email
                success = email_service.send_email(
                    to_email=user_data['email'],
                    subject="We're here to help with your lessons",
                    html_content=html_content,
                    text_content=text_content
                )
                
                if success:
                    sent_count += 1
                    logger.info(f"Support email sent to {user_data['email']} (missed: {user_data['missed_count']})")
                else:
                    failed_count += 1
                    failed_emails.append(user_data['email'])
                    logger.error(f"Failed to send support email to {user_data['email']}")
                    
            except Exception as e:
                failed_count += 1
                failed_emails.append(user_data['email'])
                logger.error(f"Error sending support email to {user_data['email']}: {e}")
        
        result = {
            'total_users': len(users_with_misses),
            'emails_sent': sent_count,
            'emails_failed': failed_count,
            'failed_emails': failed_emails,
            'success': sent_count > 0
        }
        
        logger.info(f"Support email job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in send_support_email_to_struggling_users: {e}")
        return {
            'total_users': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'failed_emails': [],
            'success': False,
            'error': str(e)
        }


def send_support_email_to_user(db: Session, user_id: int, custom_message: str = None) -> bool:
    """
    Send a support email to a specific user
    
    Args:
        db: Database session
        user_id: ID of the user to send email to
        custom_message: Optional custom message to include
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        # Get user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return False
        
        user_data = {
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'username': user.username,
            'missed_count': 0
        }
        
        # Create email content
        html_content, text_content = create_support_email_content(user_data)
        
        # Add custom message if provided
        if custom_message:
            html_content = html_content.replace(
                "We're here to support you on your leadership journey.",
                f"{custom_message}<br><br>We're here to support you on your leadership journey."
            )
            text_content = text_content.replace(
                "We're here to support you on your leadership journey.",
                f"{custom_message}\n\nWe're here to support you on your leadership journey."
            )
        
        # Send email
        email_service = EmailService()
        success = email_service.send_email(
            to_email=user.email,
            subject="We're here to help with your lessons",
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            logger.info(f"Support email sent to user {user_id} ({user.email})")
        else:
            logger.error(f"Failed to send support email to user {user_id} ({user.email})")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending support email to user {user_id}: {e}")
        return False
