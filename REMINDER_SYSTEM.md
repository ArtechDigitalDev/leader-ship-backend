# Reminder System Documentation

## Overview
Optimized stateless reminder system that sends notifications to users who haven't completed their daily lessons.

---

## 🎯 Reminder Types

| Type | Description | Behavior |
|------|-------------|----------|
| `"0"` | No reminders | User will NOT receive any reminders |
| `"1"` | One reminder | User receives 1 reminder at `reminder_time` |
| `"2"` | Two reminders | User receives 2 reminders (at `reminder_time` + 2 hours later) |

---

## ⚙️ How It Works

### **Scheduler Configuration:**
```python
# Runs every hour at minute 0
scheduler.add_job(
    daily_reminder_job,
    trigger=CronTrigger(minute=0),  # Every hour: 00:00, 01:00, 02:00, ...
    id='hourly_reminder',
    name='Hourly Reminder Job'
)
```

### **Logic Flow:**

```
1. Scheduler runs every hour
   ↓
2. Get current hour (e.g., 14)
   ↓
3. Query ONLY users whose reminder_time matches current hour
   - reminder_time LIKE "14:%" → Users with 14:00, 14:30, etc.
   - For type "2": Also check (current_hour - 2) for follow-ups
   ↓
4. For each candidate user:
   - Check: Is today in active_days?
   - Check: Does user have AVAILABLE (uncompleted) lessons?
   - Check: Should send based on reminder_type?
   ↓
5. Send reminder if all checks pass
   ↓
6. Auto-stop when lesson completed (status → COMPLETED)
```

---

## 📊 Examples

### **Example 1: reminder_type = "0" (No Reminders)**

```json
User Preferences:
{
  "reminder_time": "14:00",
  "reminder_type": "0",
  "reminder_enabled": "false"
}

Timeline:
09:00 - Lesson unlocked (AVAILABLE)
14:00 - Reminder job runs → Type "0" → SKIP ❌
16:00 - Reminder job runs → Type "0" → SKIP ❌

Result: No reminders sent
```

---

### **Example 2: reminder_type = "1" (Single Reminder)**

```json
User Preferences:
{
  "reminder_time": "14:00",
  "reminder_type": "1",
  "reminder_enabled": "true",
  "active_days": ["mon", "tue", "wed", "thu", "fri"]
}

Timeline:
09:00 - Lesson unlocked (AVAILABLE)
13:00 - Reminder job runs → Hour mismatch (13 ≠ 14) → SKIP
14:00 - Reminder job runs → Match! ✅ → Send reminder #1 📧
15:00 - Reminder job runs → Hour mismatch (15 ≠ 14) → SKIP
16:00 - Reminder job runs → Hour mismatch (16 ≠ 14) → SKIP

Result: 1 reminder at 14:00
```

---

### **Example 3: reminder_type = "2" (Two Reminders)**

```json
User Preferences:
{
  "reminder_time": "14:00",
  "reminder_type": "2",
  "reminder_enabled": "true",
  "active_days": ["mon", "tue", "wed", "thu", "fri"]
}

Timeline:
09:00 - Lesson unlocked (AVAILABLE)
13:00 - Reminder job runs → No match → SKIP
14:00 - Reminder job runs → Match (14 == 14) ✅ → Send reminder #1 📧
15:00 - Reminder job runs → No match → SKIP
16:00 - Reminder job runs → Match (16 == 14+2) ✅ → Send reminder #2 📧
17:00 - Reminder job runs → No match → SKIP

Result: 2 reminders (at 14:00 and 16:00)
```

---

### **Example 4: Lesson Completed Between Reminders**

```json
User Preferences:
{
  "reminder_time": "14:00",
  "reminder_type": "2"
}

Timeline:
09:00 - Lesson unlocked (AVAILABLE)
14:00 - Reminder job runs → Send reminder #1 ✅
15:30 - User completes lesson (AVAILABLE → COMPLETED) ✅
16:00 - Reminder job runs → No AVAILABLE lessons → SKIP ❌

Result: Only 1 reminder sent (auto-stopped after completion!)
```

---

### **Example 5: Inactive Day**

```json
User Preferences:
{
  "reminder_time": "14:00",
  "reminder_type": "2",
  "active_days": ["mon", "wed", "fri"]  // Tuesday not included
}

Timeline (Tuesday):
09:00 - Lesson NOT unlocked (Tuesday not in active_days)
14:00 - Reminder job runs → Day check fails → SKIP ❌
16:00 - Reminder job runs → Day check fails → SKIP ❌

Result: No reminders on inactive days
```

---

## 🔧 Database Optimization

### **Query Optimization:**

**Before (Inefficient):**
```python
# Fetch ALL users with reminders enabled
all_users = db.query(UserPreferences).filter(
    reminder_enabled == "true"
).all()  # Returns 10,000 users

# Then check in loop
for user in all_users:  # Process 10,000 users
    if current_hour == reminder_hour:  # Only 400 match
        send_reminder()
```

**After (Optimized):**
```python
# Fetch ONLY users whose reminder_time matches current hour
candidates = db.query(UserPreferences).filter(
    reminder_enabled == "true",
    reminder_type != "0",
    or_(
        reminder_time.like("14:%"),  # Current hour
        and_(
            reminder_type == "2",
            reminder_time.like("12:%")  # Follow-up hour (14-2)
        )
    )
).all()  # Returns ~400 users

# Process only relevant users
for user in candidates:  # Process 400 users (96% reduction!)
    send_reminder()
```

**Performance Gain:**
- 📊 **Query Size:** 10,000 → 400 users (96% reduction)
- ⚡ **Speed:** 25x faster
- 💾 **Memory:** 96% less data loaded

---

## 🚀 Auto-Sync Logic

When user updates `reminder_type` or `reminder_enabled`, they automatically sync:

### **Sync Rule 1: reminder_type affects reminder_enabled**
```python
# User sets reminder_type = "0"
{
  "reminder_type": "0"
}

# System auto-updates:
{
  "reminder_type": "0",
  "reminder_enabled": "false"  // Auto-set!
}
```

### **Sync Rule 2: reminder_enabled affects reminder_type**
```python
# User disables reminders
{
  "reminder_enabled": "false"
}

# System auto-updates:
{
  "reminder_enabled": "false",
  "reminder_type": "0"  // Auto-set!
}
```

---

## 📝 Implementation Details

### **Key Features:**

1. ✅ **Stateless**: No reminder logs needed
2. ✅ **Optimized**: Only queries relevant users
3. ✅ **Self-Correcting**: Auto-stops when lesson completed
4. ✅ **Flexible**: User controls timing and frequency
5. ✅ **Scalable**: Handles 10,000+ users efficiently

### **Edge Cases Handled:**

1. **Hour Wrap-around:**
   ```python
   reminder_time = "23:00"
   reminder_type = "2"
   
   23:00 - Reminder #1 ✅
   01:00 - Reminder #2 ✅ (23+2 % 24 = 1)
   ```

2. **Inactive Days:**
   ```python
   active_days = ["mon", "wed", "fri"]
   
   Tuesday - No reminders ❌
   Wednesday - Reminders sent ✅
   ```

3. **Completed Lessons:**
   ```python
   14:00 - Reminder sent (lesson AVAILABLE)
   15:00 - User completes (AVAILABLE → COMPLETED)
   16:00 - No reminder (no AVAILABLE lessons) ✅
   ```

---

## 🔮 Future Enhancements

### **Notification Channels:**

```python
# Email Integration
from sendgrid import SendGridAPIClient

def send_email_reminder(user_id, message):
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    sg.send(...)

# Push Notification Integration
from firebase_admin import messaging

def send_push_reminder(user_id, message):
    messaging.send(...)

# SMS Integration
from twilio.rest import Client

def send_sms_reminder(user_id, message):
    client = Client(account_sid, auth_token)
    client.messages.create(...)
```

### **Personalized Messages:**

```python
# Current
"You have 3 lesson(s) to complete today!"

# Future: Category-specific
"Complete 'Clarity - Week 1, Day 3' before day ends!"

# Future: Motivational
"You're on a 5-day streak! Don't break it - complete today's lesson!"
```

### **Smart Timing:**

```python
# Current: Fixed 2-hour gap
14:00 - Reminder #1
16:00 - Reminder #2

# Future: Dynamic based on user behavior
14:00 - Reminder #1
17:00 - Reminder #2 (user usually completes between 16-18)
```

---

## 📊 Monitoring & Metrics

**Recommended Metrics to Track:**

1. **Reminder Effectiveness:**
   - % of users who complete after 1st reminder
   - % of users who complete after 2nd reminder
   - % of users who never complete

2. **Optimal Timing:**
   - Best reminder_time for completion rates
   - Best gap between reminders (currently 2 hours)

3. **User Preferences:**
   - Most popular reminder_type distribution
   - Most popular reminder_time distribution
   - Most popular active_days patterns

---

## ✅ Summary

**Reminder System Benefits:**

| Feature | Status | Description |
|---------|--------|-------------|
| Optimized Query | ✅ | Only fetches relevant users (96% reduction) |
| Stateless | ✅ | No reminder logs needed |
| Auto-Stop | ✅ | Stops when lesson completed |
| Flexible | ✅ | User controls timing and frequency |
| Scalable | ✅ | Handles 10,000+ users efficiently |
| Type 0 | ✅ | No reminders |
| Type 1 | ✅ | One reminder at reminder_time |
| Type 2 | ✅ | Two reminders (initial + follow-up) |

**Ready for Production!** 🚀

