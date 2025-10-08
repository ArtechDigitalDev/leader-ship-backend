# User Preferences API Documentation

## Overview
User preferences API allows users to view and customize their learning experience settings.

## Endpoints

### 1. Get User Preferences
**Endpoint:** `GET /api/v1/user-preferences/`

**Description:** Retrieve current user's learning preferences

**Authentication:** Required (Bearer Token)

**Request:**
```bash
GET /api/v1/user-preferences/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "User preferences retrieved successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "frequency": "daily",
    "active_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "lesson_time": "09:00",
    "timezone": "ET",
    "days_between_lessons": 1,
    "reminder_enabled": "true",
    "reminder_time": "14:00",
    "reminder_type": "1"
  },
  "meta": null
}
```

---

### 2. Update User Preferences
**Endpoint:** `PUT /api/v1/user-preferences/`

**Description:** Update current user's learning preferences (all fields optional)

**Authentication:** Required (Bearer Token)

**Request:**
```bash
PUT /api/v1/user-preferences/
Authorization: Bearer {token}
Content-Type: application/json

{
  "frequency": "daily",
  "active_days": ["mon", "wed", "fri"],
  "lesson_time": "10:00",
  "timezone": "ET",
  "days_between_lessons": 2,
  "reminder_enabled": "true",
  "reminder_time": "15:00",
  "reminder_type": "1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User preferences updated successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "frequency": "daily",
    "active_days": ["mon", "wed", "fri"],
    "lesson_time": "10:00",
    "timezone": "ET",
    "days_between_lessons": 2,
    "reminder_enabled": "true",
    "reminder_time": "15:00",
    "reminder_type": "1"
  },
  "meta": null
}
```

---

## Field Descriptions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `frequency` | string | "daily" | Learning frequency preference |
| `active_days` | array | All days | Days when lessons should be available (mon, tue, wed, thu, fri, sat, sun) |
| `lesson_time` | string | "09:00" | Preferred lesson delivery time in HH:MM format (24-hour) |
| `timezone` | string | "ET" | User's timezone |
| `days_between_lessons` | integer | 1 | Number of days between lesson unlocks |
| `reminder_enabled` | string | "true" | Enable/disable reminders ("true" or "false") |
| `reminder_time` | string | "14:00" | Reminder time in HH:MM format (24-hour) |
| `reminder_type` | string | "1" | Reminder type (1=email, 2=push notification, etc.) |

---

## Examples

### Example 1: Weekend Learner
**Scenario:** User wants lessons only on weekends at 10 AM

**Request:**
```json
{
  "active_days": ["sat", "sun"],
  "lesson_time": "10:00"
}
```

**Result:** Lessons will unlock only on Saturdays and Sundays at 10:00 AM

---

### Example 2: Slow Paced Learner
**Scenario:** User wants lessons every 3 days, weekdays only

**Request:**
```json
{
  "active_days": ["mon", "tue", "wed", "thu", "fri"],
  "days_between_lessons": 3,
  "lesson_time": "08:00"
}
```

**Result:** Lessons will unlock every 3 days on weekdays at 8:00 AM

---

### Example 3: Disable Reminders
**Scenario:** User wants to disable all reminders

**Request:**
```json
{
  "reminder_enabled": "false"
}
```

**Result:** User will not receive any reminder notifications

---

## How Lesson Unlocking Works

1. **Scheduler runs every hour** (at minute 0)
2. **Checks user preferences:**
   - Is today in user's `active_days`?
   - Does current hour match `lesson_time` hour?
3. **Validates lesson status:**
   - Previous lesson must be completed
   - Lesson must be LOCKED
4. **Unlocks lesson** if all conditions are met

### Flow Diagram:
```
User Registration
    ↓
Default Preferences Created
    ↓
User Updates Preferences (Optional)
    ↓
Scheduler Checks Every Hour
    ↓
Active Day? → Correct Time? → Previous Lesson Complete?
    ↓
Lesson Unlocked ✅
```

---

## Error Responses

### 404 Not Found
```json
{
  "success": false,
  "message": "User preferences not found",
  "data": null
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "message": "Not authenticated",
  "data": null
}
```

---

## Notes

- All fields in UPDATE request are optional
- Only provided fields will be updated
- Changes take effect on next scheduler run
- Default preferences are created automatically during registration
- Times are in 24-hour format (HH:MM)
- Day names must be lowercase 3-letter abbreviations (mon, tue, wed, thu, fri, sat, sun)

