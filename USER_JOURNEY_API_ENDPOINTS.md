# User Journey System API Endpoints

## Overview
Complete API endpoints for the user journey system. All endpoints require authentication and return standardized responses.

## Base URL
All endpoints are prefixed with `/api/v1/`

## Authentication
All endpoints require Bearer token authentication via the `Authorization` header.

## User Journeys API

### Start New Journey
**POST** `/user-journeys/start`

Start a new user journey based on assessment results.

**Request Body:**
```json
{
  "assessment_result_id": 123
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 456,
  "assessment_result_id": 123,
  "growth_focus_category": "clarity",
  "intentional_advantage_category": "connection",
  "current_category": "clarity",
  "status": "active",
  "started_at": "2024-01-15T10:30:00Z",
  "total_categories_completed": 0,
  "total_weeks_completed": 0,
  "total_lessons_completed": 0
}
```

### Get Active Journey
**GET** `/user-journeys/active`

Get the currently active journey for the user.

**Response:**
```json
{
  "id": 1,
  "user_id": 456,
  "assessment_result_id": 123,
  "growth_focus_category": "clarity",
  "intentional_advantage_category": "connection",
  "current_category": "clarity",
  "status": "active",
  "started_at": "2024-01-15T10:30:00Z",
  "total_categories_completed": 0,
  "total_weeks_completed": 0,
  "total_lessons_completed": 0
}
```

### Get Specific Journey
**GET** `/user-journeys/{journey_id}`

Get a specific journey by ID.

### Get All User Journeys
**GET** `/user-journeys/`

Get all journeys for the current user.

### Update Journey
**PUT** `/user-journeys/{journey_id}`

Update journey settings.

**Request Body:**
```json
{
  "current_category": "consistency",
  "status": "paused"
}
```

### Complete Category
**POST** `/user-journeys/{journey_id}/complete-category`

Complete current category and move to next one.

### Delete/Pause Journey
**DELETE** `/user-journeys/{journey_id}`

Soft delete journey by marking as paused.

## User Lessons API

### Get Available Lessons
**GET** `/user-lessons/available`

Get all available lessons for the current user.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 456,
    "user_journey_id": 1,
    "daily_lesson_id": 5,
    "status": "available",
    "points_earned": 0,
    "days_between_lessons": 1,
    "unlocked_at": "2024-01-15T10:30:00Z",
    "started_at": null,
    "completed_at": null,
    "daily_lesson_title": "Understanding Your Values",
    "daily_lesson_day_number": 1,
    "week_topic": "clarity",
    "week_number": 1
  }
]
```

### Get Lessons by Category
**GET** `/user-lessons/category/{category}`

Get all lessons for a specific category.

**Example:** `/user-lessons/category/clarity`

### Get Specific Lesson
**GET** `/user-lessons/{lesson_id}`

Get a specific lesson with details.

### Start Lesson
**POST** `/user-lessons/{lesson_id}/start`

Mark a lesson as started.

**Response:**
```json
{
  "id": 1,
  "user_id": 456,
  "user_journey_id": 1,
  "daily_lesson_id": 5,
  "status": "available",
  "points_earned": 0,
  "started_at": "2024-01-15T11:00:00Z"
}
```

### Complete Lesson
**POST** `/user-lessons/{lesson_id}/complete`

Complete a lesson and award points.

**Request Body:**
```json
{
  "points_earned": 20,
  "completion_notes": "Great lesson, learned a lot about values"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 456,
  "user_journey_id": 1,
  "daily_lesson_id": 5,
  "status": "completed",
  "points_earned": 20,
  "completed_at": "2024-01-15T12:00:00Z"
}
```

### Manually Unlock Lesson
**PUT** `/user-lessons/{lesson_id}/unlock`

Manually unlock a lesson (bypass timing restrictions).

### Update Lesson Settings
**PUT** `/user-lessons/{lesson_id}/settings`

Update lesson progression settings.

**Query Parameters:**
- `days_between_lessons`: 0-7 (days to wait before next lesson unlocks)

### Unlock Due Lessons
**POST** `/user-lessons/unlock-due`

Manually trigger unlocking of due lessons.

**Response:**
```json
{
  "message": "Unlocked 2 lessons",
  "unlocked_count": 2,
  "success": true
}
```

### Get Lessons Due for Unlock
**GET** `/user-lessons/due/unlock`

Get lessons that are due to be unlocked (for debugging).

## User Progress API

### Get User Progress
**GET** `/user-progress/`

Get user progress overview.

**Response:**
```json
{
  "id": 1,
  "user_id": 456,
  "total_points_earned": 150,
  "total_lessons_completed": 6,
  "total_weeks_completed": 2,
  "total_categories_completed": 0,
  "current_journey_id": 1,
  "current_category": "clarity",
  "current_week_number": 2,
  "current_streak_days": 5,
  "longest_streak_days": 7,
  "last_activity_date": "2024-01-15",
  "created_at": "2024-01-10T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### Get Detailed Progress Stats
**GET** `/user-progress/stats`

Get detailed progress statistics with calculated metrics.

**Response:**
```json
{
  "user_id": 456,
  "total_points_earned": 150,
  "total_lessons_completed": 6,
  "total_weeks_completed": 2,
  "total_categories_completed": 0,
  "current_category": "clarity",
  "current_week_number": 2,
  "current_streak_days": 5,
  "longest_streak_days": 7,
  "last_activity_date": "2024-01-15",
  "average_points_per_lesson": 25.0,
  "completion_rate": 75.0,
  "days_since_last_activity": 0,
  "next_milestone": "Complete 10 lessons"
}
```

### Update Progress Settings
**PUT** `/user-progress/`

Update user progress settings.

**Request Body:**
```json
{
  "current_category": "consistency",
  "current_week_number": 1
}
```

### Internal Progress Updates
These endpoints are typically called internally by other services:

- **POST** `/user-progress/lesson-completed` - Update on lesson completion
- **POST** `/user-progress/week-completed` - Update on week completion  
- **POST** `/user-progress/category-completed` - Update on category completion
- **POST** `/user-progress/reset-streak` - Reset streak if broken

### Get User Milestones
**GET** `/user-progress/milestones`

Get user achievements and next milestones.

**Response:**
```json
{
  "achievements": [
    {
      "name": "First Lesson",
      "description": "Completed your first lesson",
      "earned": true
    },
    {
      "name": "5 Lessons Complete",
      "description": "Completed 5 lessons", 
      "earned": true
    }
  ],
  "next_milestones": [
    {
      "name": "7-Day Streak",
      "description": "Build a 7-day learning streak",
      "target": 7,
      "current": 5
    }
  ]
}
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "message": "Error description",
  "success": false,
  "status_code": 400
}
```

Common error codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Usage Examples

### Complete User Journey Flow

1. **Start Journey:**
   ```bash
   POST /api/v1/user-journeys/start
   {"assessment_result_id": 123}
   ```

2. **Get Available Lessons:**
   ```bash
   GET /api/v1/user-lessons/available
   ```

3. **Start a Lesson:**
   ```bash
   POST /api/v1/user-lessons/1/start
   ```

4. **Complete a Lesson:**
   ```bash
   POST /api/v1/user-lessons/1/complete
   {"points_earned": 20}
   ```

5. **Check Progress:**
   ```bash
   GET /api/v1/user-progress/stats
   ```

6. **Complete Category:**
   ```bash
   POST /api/v1/user-journeys/1/complete-category
   ```

## Integration Notes

- All endpoints require authentication
- Progress updates are automatically handled by the services
- Lesson unlocking can be manual or automatic based on timing
- The system supports flexible lesson pacing
- Background jobs can be set up for automatic lesson unlocking
