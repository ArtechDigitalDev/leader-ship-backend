# User Journey System Implementation

## Overview
Complete implementation of the user journey system for the 5Cs Leadership Assessment platform. This system tracks user progress through lessons, manages journey flow, and maintains comprehensive progress statistics.

## Database Tables

### 1. **user_journeys**
- **Purpose**: Track individual user journeys through the 5Cs program
- **Key Features**:
  - Links to assessment results to determine growth focus and intentional advantage
  - Tracks current category being worked on
  - Maintains overall journey progress statistics
  - Supports journey status (active, completed, paused)

### 2. **user_lessons**
- **Purpose**: Track individual lesson completion and progress
- **Key Features**:
  - Links users to specific daily lessons
  - Tracks lesson status (locked, available, completed)
  - Supports user-defined lesson timing (days between lessons)
  - Records points earned and completion timestamps

### 3. **user_progress**
- **Purpose**: Maintain overall user statistics across all journeys
- **Key Features**:
  - One row per user (updated, not inserted)
  - Tracks total points, lessons, weeks, and categories completed
  - Maintains current status and streak information
  - Provides comprehensive progress statistics

## Models Created

### Models
- `app/models/user_journey.py` - UserJourney model with JourneyStatus enum
- `app/models/user_lesson.py` - UserLesson model with LessonStatus enum  
- `app/models/user_progress.py` - UserProgress model for overall stats

### Schemas
- `app/schemas/user_journey.py` - Pydantic schemas for user journey operations
- `app/schemas/user_lesson.py` - Pydantic schemas for lesson operations
- `app/schemas/user_progress.py` - Pydantic schemas for progress tracking

### Services
- `app/services/user_journey_service.py` - Business logic for journey management
- `app/services/user_lesson_service.py` - Business logic for lesson progression
- `app/services/user_progress_service.py` - Business logic for progress tracking

## Key Features Implemented

### 1. Journey Initialization
- Automatically creates user journey based on assessment results
- Sets growth focus as starting category
- Initializes lessons for the starting category
- Creates user progress record

### 2. Lesson Progression
- Progressive unlocking of lessons based on user-defined timing
- Support for immediate unlock or delayed unlock (1-3 days)
- Automatic next lesson unlocking when previous is completed
- Background job support for scheduled unlocks

### 3. Category Progression
- Automatic progression through all 5 categories
- Category completion triggers next category initialization
- Journey completion when all categories are finished

### 4. Progress Tracking
- Real-time progress updates
- Streak tracking and maintenance
- Comprehensive statistics calculation
- Milestone identification

### 5. User Experience
- Flexible lesson timing (user can set 1/2/3 days between lessons)
- Manual lesson unlocking capability
- Progress visualization support
- Achievement tracking foundation

## Data Flow

### Assessment Completion Flow
```
1. User completes 5Cs Assessment → assessment_results table
2. Calculate Growth Focus (lowest score) & Intentional Advantage (highest score)
3. User clicks "Start Your Growth" button
4. Create user_journey record with Growth Focus as starting category
5. Initialize user_lessons for Growth Focus category (first lesson available)
6. Create/update user_progress record
```

### Lesson Completion Flow
```
1. User completes lesson → user_lessons table updated
2. Award points and mark completion timestamp
3. Update user_progress statistics
4. Check if next lesson should be unlocked
5. Unlock next lesson if timing conditions are met
6. Check for category completion
7. Move to next category if current is complete
```

### Background Processing
```
1. Daily job runs to unlock lessons due for release
2. Streak maintenance and reset if broken
3. Progress statistics calculation
4. Badge eligibility checking (foundation for future implementation)
```

## API Endpoints (To Be Created)

### User Journey Endpoints
- `POST /api/user-journeys/start` - Start new journey from assessment
- `GET /api/user-journeys/active` - Get active journey
- `GET /api/user-journeys/{journey_id}` - Get specific journey
- `PUT /api/user-journeys/{journey_id}` - Update journey settings

### User Lesson Endpoints
- `GET /api/user-lessons/available` - Get available lessons
- `GET /api/user-lessons/category/{category}` - Get lessons for category
- `POST /api/user-lessons/{lesson_id}/start` - Start lesson
- `POST /api/user-lessons/{lesson_id}/complete` - Complete lesson
- `PUT /api/user-lessons/{lesson_id}/unlock` - Manually unlock lesson

### User Progress Endpoints
- `GET /api/user-progress` - Get user progress
- `GET /api/user-progress/stats` - Get detailed statistics
- `PUT /api/user-progress` - Update progress settings

## Integration Points

### With Existing System
- Integrates with existing `users`, `assessment_results`, `weeks`, and `daily_lessons` tables
- Maintains backward compatibility
- Uses existing authentication and authorization system

### UI Integration
- Supports the "Your Leadership Qualities" UI
- Provides data for lessons name UI page
- Enables progress tracking visualization
- Supports badge and achievement systems

## Next Steps

1. **Database Migration**: Create Alembic migration for new tables
2. **API Router Creation**: Implement REST endpoints using the services
3. **Background Jobs**: Set up scheduled tasks for lesson unlocking
4. **Badge System**: Implement badges_earned table and logic
5. **Testing**: Create comprehensive test suite
6. **Documentation**: Update API documentation

## Benefits

- **Organized Structure**: Clean separation of concerns with models, schemas, and services
- **Scalable Design**: Supports multiple journeys per user and complex progression rules
- **Flexible Timing**: User-controlled lesson pacing
- **Comprehensive Tracking**: Detailed progress and statistics
- **Future-Ready**: Foundation for badges, achievements, and gamification
