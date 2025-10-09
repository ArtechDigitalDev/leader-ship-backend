# Email Notification System Documentation

## Overview

This document describes the email notification system integrated with the Leadership Development Platform. The system sends automated emails for lesson reminders, unlocks, and milestone achievements.

---

## Architecture

### Components

1. **Email Service (`app/utils/email.py`)**
   - Core email sending functionality
   - SMTP configuration and connection handling
   - Email template management

2. **Scheduler Integration (`app/services/scheduler_service.py`)**
   - Automatic reminder emails based on user preferences
   - Integration with reminder system logic

3. **Configuration (`app/core/config.py`)**
   - SMTP settings and credentials
   - Email branding (FROM_EMAIL, FROM_NAME)

---

## Features

### 1. Lesson Reminder Emails

**Trigger:** Scheduled based on user preferences (reminder_time)

**Types:**
- **Initial Reminder:** Sent at the user's preferred reminder_time
- **Follow-up Reminder:** Sent 2 hours after initial (for type "2" users only)

**Content:**
- Number of available lessons
- Call-to-action button to complete lessons
- Personalized greeting with user's name
- Professional HTML template with branding

**Example:**
```
Subject: Your Leadership Lesson is Ready!

Hello John,

You have 3 new lessons available to complete!

Continue your leadership development journey by completing your lesson today.

[Complete Your Lesson Now]
```

---

### 2. Lesson Unlock Notifications

**Trigger:** When a new lesson is unlocked for a user

**Content:**
- Lesson title
- Week and day number
- Direct link to start the lesson

**Example:**
```
Subject: New Lesson Unlocked: Week 2, Day 5

Hello John,

Great news! A new lesson is now available for you.

Strategic Decision Making
Week: 2 | Day: 5

[Start Learning Now]
```

---

### 3. Streak Milestone Emails

**Trigger:** When user achieves significant streak milestones (7, 14, 30, 60, 90 days)

**Content:**
- Current streak count
- Congratulatory message
- Encouragement to continue

**Example:**
```
Subject: Amazing! 30-Day Streak Achieved!

Hi John,

You've achieved a 30-Day Streak!

Your consistency is truly inspiring!
```

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Leadership Development
APP_URL=https://your-app-url.com
```

### Gmail Setup (Recommended for Testing)

1. **Enable 2-Factor Authentication**
   - Go to Google Account Settings
   - Security → 2-Step Verification

2. **Generate App Password**
   - Go to Security → App passwords
   - Select "Mail" and your device
   - Copy the 16-character password
   - Use this as `SMTP_PASSWORD`

3. **Configuration:**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App password
   FROM_EMAIL=your-email@gmail.com
   ```

### Production SMTP Services

#### SendGrid
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### AWS SES
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

#### Mailgun
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
```

---

## Email Templates

### HTML Template Structure

All emails use responsive HTML templates with:
- **Header:** Branded gradient background with logo/title
- **Content:** Main message body with clear typography
- **Call-to-Action:** Prominent button linking to app
- **Footer:** Unsubscribe/preferences information

### Customization

Edit templates in `app/utils/email.py`:

```python
def send_lesson_reminder(
    user_email: str,
    user_name: str,
    available_lessons: int,
    is_followup: bool = False,
    reminder_type: str = "1"
) -> bool:
    # Customize subject
    subject = "Your Leadership Lesson is Ready!"
    
    # Customize HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    ...
    </html>
    """
```

---

## Usage Examples

### Manual Email Sending

```python
from app.utils.email import send_lesson_reminder, send_lesson_unlock_notification

# Send reminder
send_lesson_reminder(
    user_email="user@example.com",
    user_name="John Doe",
    available_lessons=3,
    is_followup=False,
    reminder_type="1"
)

# Send unlock notification
send_lesson_unlock_notification(
    user_email="user@example.com",
    user_name="John Doe",
    lesson_title="Strategic Decision Making",
    week_number=2,
    day_number=5
)
```

### Automated Reminders (Scheduler)

Reminders are sent automatically via the scheduler:

```python
# In scheduler_service.py
def _send_notification(self, user_id: int, available_lessons: int, reminder_type: str, is_followup: bool):
    # Gets user details from database
    user = self.db.query(User).filter(User.id == user_id).first()
    
    # Sends email automatically
    send_lesson_reminder(
        user_email=user.email,
        user_name=user.full_name,
        available_lessons=available_lessons,
        is_followup=is_followup,
        reminder_type=reminder_type
    )
```

---

## Testing

### Test Script

Create `test_email_system.py`:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.email import send_lesson_reminder, send_lesson_unlock_notification, send_streak_milestone_email

def test_reminder_email():
    """Test lesson reminder email"""
    print("\nTesting Lesson Reminder Email...")
    success = send_lesson_reminder(
        user_email="test@example.com",
        user_name="Test User",
        available_lessons=3,
        is_followup=False,
        reminder_type="1"
    )
    print(f"Result: {'Success' if success else 'Failed'}")

def test_followup_email():
    """Test follow-up reminder email"""
    print("\nTesting Follow-up Reminder Email...")
    success = send_lesson_reminder(
        user_email="test@example.com",
        user_name="Test User",
        available_lessons=2,
        is_followup=True,
        reminder_type="2"
    )
    print(f"Result: {'Success' if success else 'Failed'}")

def test_unlock_email():
    """Test lesson unlock notification"""
    print("\nTesting Lesson Unlock Email...")
    success = send_lesson_unlock_notification(
        user_email="test@example.com",
        user_name="Test User",
        lesson_title="Strategic Decision Making",
        week_number=2,
        day_number=5
    )
    print(f"Result: {'Success' if success else 'Failed'}")

def test_streak_email():
    """Test streak milestone email"""
    print("\nTesting Streak Milestone Email...")
    success = send_streak_milestone_email(
        user_email="test@example.com",
        user_name="Test User",
        streak_days=30
    )
    print(f"Result: {'Success' if success else 'Failed'}")

if __name__ == "__main__":
    print("="*70)
    print("EMAIL NOTIFICATION SYSTEM - TEST SUITE")
    print("="*70)
    
    test_reminder_email()
    test_followup_email()
    test_unlock_email()
    test_streak_email()
    
    print("\n" + "="*70)
    print("Testing Complete!")
    print("="*70)
```

**Run:**
```bash
python test_email_system.py
```

---

## Mock Mode (Development)

When SMTP credentials are not configured, the system runs in **mock mode**:

```python
if not self.smtp_user or not self.smtp_password:
    logger.warning("SMTP credentials not configured. Email not sent.")
    logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
    return True  # Return True for development/testing
```

**Benefits:**
- No need to configure SMTP during development
- All email functionality works without actual sending
- Logs show what would have been sent
- Easy to test email logic without spam

---

## Monitoring and Logging

### Log Levels

```python
import logging

logger = logging.getLogger(__name__)

# Success
logger.info(f"Email sent successfully to {user.email}")

# Warning (non-critical issues)
logger.warning(f"SMTP credentials not configured")

# Error (failed to send)
logger.error(f"Failed to send email to {user.email}: {error}")
```

### Console Output

During reminder job execution:

```
Checking User ID: 13 (user13@example.com)...
   Reminder type: 1
   Current hour: 11
   Reminder hour: 9
   Is match: NO (not their reminder time)

Checking User ID: 14 (user14@example.com)...
   Reminder type: 2
   Current hour: 11
   Reminder hour: 9
   Follow-up hour: 11
   Is follow-up match: YES
   Active day check: YES (today is 'tue')
   Available lessons: 5
   📧 Sending email to user 14 (user14@example.com): Follow-up reminder...
   ✅ Email sent successfully!
```

---

## Error Handling

### SMTP Connection Errors

```python
try:
    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        server.send_message(message)
except smtplib.SMTPAuthenticationError:
    logger.error("SMTP authentication failed. Check credentials.")
except smtplib.SMTPException as e:
    logger.error(f"SMTP error: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
```

### User Data Errors

```python
if not user or not user.email:
    logger.warning(f"User {user_id} not found or has no email")
    return
```

---

## Best Practices

### 1. Rate Limiting

Avoid sending too many emails at once:

```python
import time

for user_id in users_to_notify:
    send_notification(user_id)
    time.sleep(0.1)  # 100ms delay between emails
```

### 2. Unsubscribe Links

Add unsubscribe functionality:

```html
<div class="footer">
    <p>You are receiving this email because you have enabled lesson reminders.</p>
    <p>
        To update your preferences, 
        <a href="https://your-app-url.com/preferences">click here</a>.
    </p>
</div>
```

### 3. Email Validation

Validate email before sending:

```python
import re

def is_valid_email(email: str) -> bool:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
```

### 4. Retry Logic

Implement retry for failed emails:

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def send_email_with_retry(to_email, subject, content):
    return send_email(to_email, subject, content)
```

---

## Performance Optimization

### Batch Processing

Process emails in batches to avoid database overload:

```python
from sqlalchemy import func

# Get users in batches
batch_size = 100
offset = 0

while True:
    users = db.query(User).offset(offset).limit(batch_size).all()
    if not users:
        break
    
    for user in users:
        send_notification(user.id)
    
    offset += batch_size
```

### Async Email Sending

For better performance, consider async:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def send_emails_async(users):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = [
            loop.run_in_executor(executor, send_email, user.email)
            for user in users
        ]
        await asyncio.gather(*tasks)
```

---

## Troubleshooting

### Issue: Emails Not Sending

**Check:**
1. SMTP credentials in `.env`
2. App password (not regular password for Gmail)
3. Network connectivity
4. SMTP host and port

**Debug:**
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Issue: Emails Going to Spam

**Solutions:**
1. Use proper FROM_EMAIL with verified domain
2. Add SPF, DKIM, DMARC records to DNS
3. Use professional SMTP service (SendGrid, SES)
4. Avoid spam trigger words in subject/body
5. Include unsubscribe link

### Issue: Gmail "Less Secure Apps"

**Solution:** Use App Passwords instead of enabling "Less secure app access"

---

## Future Enhancements

### 1. Email Templates System

```python
from jinja2 import Template

template = Template("""
<html>
    <body>
        <h1>Hello {{ user_name }}!</h1>
        <p>You have {{ lesson_count }} lessons.</p>
    </body>
</html>
""")

html = template.render(user_name="John", lesson_count=3)
```

### 2. Email Analytics

Track email metrics:
- Open rates
- Click-through rates
- Bounce rates
- Unsubscribe rates

### 3. A/B Testing

Test different email templates:
```python
def get_email_template(user_id: int):
    # 50% users get template A, 50% get template B
    return "template_a" if user_id % 2 == 0 else "template_b"
```

### 4. Personalization

Advanced personalization:
```python
def get_personalized_content(user):
    if user.streak_days > 7:
        return "You're on fire! Keep the momentum going!"
    else:
        return "Start building your learning streak today!"
```

---

## Summary

The email notification system provides:

✅ **Automated Reminders** - Based on user preferences
✅ **Professional Templates** - Responsive HTML design
✅ **Multiple Email Types** - Reminders, unlocks, milestones
✅ **Mock Mode** - Development without SMTP
✅ **Error Handling** - Graceful failure management
✅ **Logging** - Comprehensive tracking
✅ **Flexible Configuration** - Environment-based settings
✅ **Production Ready** - Supports major SMTP providers

---

## Support

For issues or questions:
- Check logs: `logger.error()` messages
- Review SMTP configuration
- Test with `test_email_system.py`
- Verify user has valid email address

---

**Last Updated:** October 9, 2025
**Version:** 1.0.0

