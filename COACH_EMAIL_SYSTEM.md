# Coach Custom Email System Documentation

## Overview

This feature allows coaches to send custom emails to participants directly from the dashboard. Coaches can write their own subject and message content, making it perfect for intervention, encouragement, or personalized communication based on the `current_lesson_missed_count`.

---

## 🎯 Use Cases

### 1. **Intervention Email** (3+ misses)
Coach sees a participant has missed their current lesson 3+ times and sends a supportive intervention email.

### 2. **Encouragement Email** (1-2 misses)
Coach sends a gentle reminder or motivational message to participants who are slightly behind.

### 3. **Bulk Communication**
Coach sends the same message to multiple participants at once.

### 4. **Custom Messages**
Coach can personalize emails for specific situations or achievements.

---

## 📡 API Endpoints

### 1. Send Email to Single Participant

**Endpoint:** `POST /api/v1/coach/send-email`

**Authentication:** Required (Coach role)

**Request Body:**
```json
{
  "participant_email": "participant@example.com",
  "subject": "Let's catch up on your progress",
  "message": "Hi there!\n\nI noticed you've missed a few lessons. I'm here to help!\n\nLet's schedule a quick call to discuss any challenges you're facing.\n\nBest regards,\nYour Coach"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Email sent successfully to participant@example.com",
  "data": {
    "sent_count": 1
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "detail": "Participant with email participant@example.com not found"
}
```

---

### 2. Send Bulk Email to Multiple Participants

**Endpoint:** `POST /api/v1/coach/send-bulk-email`

**Authentication:** Required (Coach role)

**Request Body:**
```json
{
  "participant_emails": [
    "participant1@example.com",
    "participant2@example.com",
    "participant3@example.com"
  ],
  "subject": "Weekly Check-in",
  "message": "Hello everyone!\n\nI hope you're doing well on your leadership journey.\n\nRemember, I'm here to support you!\n\nBest,\nYour Coach"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Email sent to 3 out of 3 participants",
  "data": {
    "sent_count": 3
  }
}
```

**Response (Partial Success):**
```json
{
  "success": true,
  "message": "Email sent to 2 out of 3 participants",
  "data": {
    "sent_count": 2,
    "failed_emails": ["invalid@example.com"]
  }
}
```

---

## 📧 Email Template

### Plain Text Message

Coach provides plain text:
```
Hi John,

I noticed you've been having trouble completing your current lesson.

Is there anything I can help with?

Best regards,
Coach Sarah
```

**Result:** Automatically converted to beautiful HTML with:
- Professional header with gradient
- Proper formatting
- Coach signature
- Footer with platform info

---

### HTML Message

Coach can also provide HTML for custom formatting:
```html
<h2>Great Job!</h2>
<p>You're doing amazing work!</p>
<ul>
  <li>Completed 10 lessons</li>
  <li>5-day streak</li>
  <li>Keep it up!</li>
</ul>
```

**Result:** Wrapped in professional template with header and footer.

---

## 🎨 Email Design

### Template Features

```html
✅ Professional gradient header
✅ Responsive design (mobile/desktop)
✅ Clear typography
✅ Coach name signature
✅ Platform branding footer
✅ Plain text fallback
```

### Example HTML Output

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
      border-radius: 10px 10px 0 0;
    }
    .content {
      background: #f9f9f9;
      padding: 30px;
      border-radius: 0 0 10px 10px;
    }
    .footer {
      text-align: center;
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #ddd;
      color: #666;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📧 Message from Your Coach</h1>
  </div>
  <div class="content">
    <p>Hello John,</p>
    <p>I noticed you've missed...</p>
    <p>
      Best regards,<br>
      <strong>Coach Sarah</strong>
    </p>
  </div>
  <div class="footer">
    <p>This email was sent by your coach through the Leadership Development Platform.</p>
  </div>
</body>
</html>
```

---

## 💻 Frontend Integration Examples

### 1. Send Email to Single Participant

```javascript
async function sendInterventionEmail(participantEmail, missCount) {
  const response = await fetch('/api/v1/coach/send-email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      participant_email: participantEmail,
      subject: `Let's Address Your Progress Together`,
      message: `Hi there!

I've noticed you've missed your current lesson ${missCount} times. 

I want to help you get back on track! Can we schedule a quick call to discuss any challenges you're facing?

Remember, everyone's learning journey is unique, and I'm here to support you.

Best regards,
Your Coach`
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    showNotification('Email sent successfully!', 'success');
  } else {
    showNotification('Failed to send email', 'error');
  }
}
```

### 2. Send Bulk Email to Multiple Participants

```javascript
async function sendBulkEmail(participantEmails, subject, message) {
  const response = await fetch('/api/v1/coach/send-bulk-email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      participant_emails: participantEmails,
      subject: subject,
      message: message
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    const { sent_count, failed_emails } = result.data;
    
    let message = `Email sent to ${sent_count} participants!`;
    if (failed_emails && failed_emails.length > 0) {
      message += `\nFailed: ${failed_emails.join(', ')}`;
    }
    
    showNotification(message, 'success');
  } else {
    showNotification('Failed to send emails', 'error');
  }
}
```

### 3. Dashboard Integration with Miss Count

```javascript
function ParticipantRow({ participant }) {
  const handleSendEmail = () => {
    let subject, message;
    
    if (participant.current_lesson_missed_count >= 3) {
      // Intervention email
      subject = "Let's Get You Back on Track";
      message = `Hi ${participant.user_name},

I've noticed you've been having trouble with your current lesson. 

I'm here to help! Let's schedule a quick call to address any challenges.

Best regards,
Your Coach`;
    } else if (participant.current_lesson_missed_count > 0) {
      // Gentle reminder
      subject = "Quick Check-in";
      message = `Hi ${participant.user_name},

Just a friendly reminder about your current lesson!

You're doing great - keep up the momentum!

Best,
Your Coach`;
    }
    
    sendInterventionEmail(participant.email, participant.current_lesson_missed_count);
  };
  
  return (
    <tr>
      <td>{participant.user_name}</td>
      <td>{participant.email}</td>
      <td>{participant.current_lesson_missed_count}</td>
      <td>
        {participant.current_lesson_missed_count >= 3 && (
          <button onClick={handleSendEmail} className="btn-danger">
            Send Intervention Email
          </button>
        )}
        {participant.current_lesson_missed_count > 0 && participant.current_lesson_missed_count < 3 && (
          <button onClick={handleSendEmail} className="btn-warning">
            Send Reminder
          </button>
        )}
      </td>
    </tr>
  );
}
```

### 4. Bulk Email Modal

```javascript
function BulkEmailModal({ selectedParticipants, onClose }) {
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  
  const handleSend = async () => {
    const emails = selectedParticipants.map(p => p.email);
    
    await sendBulkEmail(emails, subject, message);
    onClose();
  };
  
  return (
    <div className="modal">
      <h2>Send Email to {selectedParticipants.length} Participants</h2>
      
      <div className="form-group">
        <label>Subject:</label>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Enter email subject"
        />
      </div>
      
      <div className="form-group">
        <label>Message:</label>
        <textarea
          rows="10"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your message..."
        />
      </div>
      
      <div className="actions">
        <button onClick={handleSend} className="btn-primary">
          Send Email
        </button>
        <button onClick={onClose} className="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  );
}
```

---

## 🔒 Security & Validation

### 1. **Authentication**
- Only users with `coach` role can send emails
- Token-based authentication required

### 2. **Recipient Validation**
- Validates participant exists in database
- Checks participant role is "participant"
- Returns error for invalid emails

### 3. **Email Validation**
- Uses `EmailStr` from Pydantic
- Validates email format before sending

### 4. **Error Handling**
- Graceful failure for individual emails in bulk
- Returns list of failed emails
- Logs all email attempts

---

## 📊 Use Case Examples

### Example 1: Intervention for High Miss Count

**Scenario:** Participant has missed current lesson 5 times

**Coach Action:**
```json
POST /api/v1/coach/send-email
{
  "participant_email": "john@example.com",
  "subject": "I'm Here to Help!",
  "message": "Hi John,\n\nI noticed you've been struggling with the current lesson. Let's have a quick call to identify any obstacles and get you back on track.\n\nYour success is important to me!\n\nBest,\nCoach Sarah"
}
```

---

### Example 2: Bulk Email to Behind Schedule Participants

**Scenario:** Coach filters dashboard to show all participants with 1-2 misses

**Coach Action:**
```json
POST /api/v1/coach/send-bulk-email
{
  "participant_emails": [
    "participant1@example.com",
    "participant2@example.com",
    "participant3@example.com"
  ],
  "subject": "You're Almost There!",
  "message": "Hello!\n\nI see you're a bit behind on your current lesson.\n\nNo worries - take your time and reach out if you need help!\n\nYou've got this!\n\nBest,\nCoach Sarah"
}
```

---

### Example 3: HTML Formatted Celebration Email

**Scenario:** Participant completes a milestone

**Coach Action:**
```json
POST /api/v1/coach/send-email
{
  "participant_email": "achiever@example.com",
  "subject": "Congratulations on Your Achievement!",
  "message": "<h2>🎉 Amazing Work!</h2><p>You've just completed <strong>Week 5</strong>!</p><ul><li>✅ 100% completion rate</li><li>✅ 7-day streak</li><li>✅ Excellent progress</li></ul><p>Keep up the fantastic work!</p>"
}
```

---

## 🧪 Testing

### Test Email Sending (Single)

```bash
curl -X POST "http://localhost:8000/api/v1/coach/send-email" \
  -H "Authorization: Bearer YOUR_COACH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "participant_email": "test@example.com",
    "subject": "Test Email",
    "message": "This is a test message from coach."
  }'
```

### Test Bulk Email

```bash
curl -X POST "http://localhost:8000/api/v1/coach/send-bulk-email" \
  -H "Authorization: Bearer YOUR_COACH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "participant_emails": ["test1@example.com", "test2@example.com"],
    "subject": "Bulk Test",
    "message": "This is a bulk test email."
  }'
```

---

## 📝 Summary

### Features Implemented

✅ **Single Email Sending** - Coach → One participant  
✅ **Bulk Email Sending** - Coach → Multiple participants  
✅ **Dynamic Content** - Coach writes custom subject & message  
✅ **HTML Support** - Both plain text and HTML messages  
✅ **Professional Templates** - Automatically formatted emails  
✅ **Error Handling** - Graceful failures with detailed responses  
✅ **Logging** - Complete audit trail  
✅ **Security** - Role-based access control  

### Files Created/Modified

1. **`app/schemas/coach.py`** - Added email schemas
2. **`app/utils/email.py`** - Added `send_coach_custom_email()` function
3. **`app/services/coach_service.py`** - Added email sending services
4. **`app/api/routers/coach.py`** - Added email endpoints
5. **`COACH_EMAIL_SYSTEM.md`** - This documentation

---

## 🚀 Next Steps

### Future Enhancements

1. **Email Templates Library** - Pre-written templates for common scenarios
2. **Email Scheduling** - Schedule emails for later delivery
3. **Email History** - Track all sent emails
4. **Read Receipts** - Track if emails were opened
5. **Reply Tracking** - Track participant responses
6. **Email Analytics** - Success rates, open rates, etc.

---

**Last Updated:** October 9, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

