# Lesson Unlock Process Flow

## Overview
Scheduler runs **every hour** and unlocks lessons based on user preferences and completion status.

## Complete Process Flow

```
┌─────────────────────────────────────────────┐
│   SCHEDULER RUNS (Every Hour at :00)       │
│   Example: 09:00 UTC                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 1: Filter by lesson_time               │
│                                              │
│ Get users where:                             │
│ - Has LOCKED lessons                         │
│ - lesson_time hour = current hour            │
│                                              │
│ Example:                                     │
│ Current: 09:00                               │
│ Match: lesson_time = "09:00", "09:15", etc.  │
│ Skip: lesson_time = "08:00", "10:00", etc.   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Get next lesson for each user       │
│                                              │
│ For each matched user:                       │
│ - Find their active journey                  │
│ - Get current_category                       │
│ - Find first LOCKED lesson in sequence       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Validation Checks                   │
│                                              │
│ ┌─────────────────────────────────────┐    │
│ │ Check 1: Active Day                  │    │
│ │ Is today in user's active_days?      │    │
│ │ active_days: ["mon","tue","wed",...]  │    │
│ │                                       │    │
│ │ ❌ Not active day → SKIP             │    │
│ │ ✅ Active day → Continue             │    │
│ └─────────────────────────────────────┘    │
│                   │                          │
│                   ▼                          │
│ ┌─────────────────────────────────────┐    │
│ │ Check 2: Days Since Creation        │    │
│ │ Has enough time passed?              │    │
│ │                                       │    │
│ │ days_since_creation >= days_between  │    │
│ │                                       │    │
│ │ ❌ Too soon → SKIP                   │    │
│ │ ✅ Enough time → Continue            │    │
│ └─────────────────────────────────────┘    │
│                   │                          │
│                   ▼                          │
│ ┌─────────────────────────────────────┐    │
│ │ Check 3: Previous Lesson Status     │    │
│ │                                       │    │
│ │ Three scenarios:                      │    │
│ │                                       │    │
│ │ A. No previous lesson (first)         │    │
│ │    ✅ UNLOCK                          │    │
│ │                                       │    │
│ │ B. Previous completed + enough days   │    │
│ │    days_since_completion >= days_bet │    │
│ │    ✅ UNLOCK                          │    │
│ │                                       │    │
│ │ C. Previous not completed             │    │
│ │    ❌ SKIP                            │    │
│ └─────────────────────────────────────┘    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 4: Unlock Lesson                       │
│                                              │
│ If all checks pass:                          │
│ - lesson.status = AVAILABLE                  │
│ - unlocked_count += 1                        │
│                                              │
│ Database commit                              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Complete: Return unlocked count              │
└─────────────────────────────────────────────┘
```

## Example Scenario

### User Profile
```json
{
  "user_id": 8,
  "lesson_time": "09:00",
  "active_days": ["mon", "tue", "wed", "thu", "fri"],
  "days_between_lessons": 1
}
```

### Timeline

**Monday 08:00 - Scheduler Run**
- Current hour: 8
- User lesson_time: 9
- ❌ Hour mismatch → Skip user

**Monday 09:00 - Scheduler Run**
- Current hour: 9
- User lesson_time: 9
- ✅ Hour match → Process user
  - ✅ Active day: Monday is in active_days
  - ✅ Previous lesson completed 1 day ago
  - ✅ Days between: 1 >= 1
  - **🎉 LESSON UNLOCKED!**

**Tuesday 09:00 - Scheduler Run**
- Current hour: 9
- User lesson_time: 9
- ✅ Hour match → Process user
  - ✅ Active day: Tuesday is in active_days
  - ❌ Previous lesson completed 0 days ago
  - ❌ Days between: 0 < 1
  - **❌ SKIP - Not enough time**

**Saturday 09:00 - Scheduler Run**
- Current hour: 9
- User lesson_time: 9
- ✅ Hour match → Process user
  - ❌ Active day: Saturday NOT in active_days
  - **❌ SKIP - Not active day**

## Performance Benefits

### Without Time Filtering
```
1000 users total
→ Process all 1000 users every hour
→ 24 runs/day × 1000 users = 24,000 operations/day
```

### With Time Filtering (Option A)
```
1000 users total
100 users with lesson_time="09:00"
50 users with lesson_time="10:00"
etc.

At 09:00:
→ Process only 100 users
→ Skip 900 users

Daily operations: ~4,000 (83% reduction!)
```

## Key Validation Functions

### 1. `_get_users_for_current_hour()`
Filters users by lesson_time hour

### 2. `_should_unlock_lesson()`
Validates all unlock conditions:
- Active day check
- Time since creation
- Previous lesson completion

### 3. `_is_active_day()`
Checks if today is in user's active_days

### 4. `_get_next_lesson_to_unlock()`
Finds the first LOCKED lesson in sequence

## Summary

**✅ Time-based filtering** reduces unnecessary processing
**✅ Active days** respect user preferences
**✅ Sequential unlocking** maintains learning order
**✅ Completion tracking** ensures proper progression

