# Database Migration Summary

## Migration Details
- **Migration ID**: `4d9e58619a1b`
- **Description**: "Add user journey system tables"
- **Created**: 2025-09-30 09:36:38
- **Status**: ✅ Successfully Applied

## Tables Created

### 1. **user_journeys**
```sql
CREATE TABLE user_journeys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    assessment_result_id INTEGER REFERENCES assessment_results(id),
    growth_focus_category VARCHAR(20) NOT NULL,
    intentional_advantage_category VARCHAR(20) NOT NULL,
    current_category VARCHAR(20) NOT NULL,
    status journeystatus NOT NULL DEFAULT 'ACTIVE',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    total_categories_completed INTEGER DEFAULT 0,
    total_weeks_completed INTEGER DEFAULT 0,
    total_lessons_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL
);
```

### 2. **user_lessons**
```sql
CREATE TABLE user_lessons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    user_journey_id INTEGER REFERENCES user_journeys(id),
    daily_lesson_id INTEGER REFERENCES daily_lessons(id),
    status lessonstatus NOT NULL DEFAULT 'LOCKED',
    points_earned INTEGER DEFAULT 0,
    unlocked_at TIMESTAMP WITH TIME ZONE NULL,
    started_at TIMESTAMP WITH TIME ZONE NULL,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    days_between_lessons INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL
);
```

### 3. **user_progress**
```sql
CREATE TABLE user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    total_points_earned INTEGER DEFAULT 0,
    total_lessons_completed INTEGER DEFAULT 0,
    total_weeks_completed INTEGER DEFAULT 0,
    total_categories_completed INTEGER DEFAULT 0,
    current_journey_id INTEGER REFERENCES user_journeys(id),
    current_category VARCHAR(20) NULL,
    current_week_number INTEGER NULL,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_activity_date DATE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL
);
```

## Enums Created

### 1. **journeystatus**
- `ACTIVE`
- `COMPLETED` 
- `PAUSED`

### 2. **lessonstatus**
- `LOCKED`
- `AVAILABLE`
- `COMPLETED`

## Indexes Created
- `ix_user_journeys_id` on user_journeys(id)
- `ix_user_lessons_id` on user_lessons(id)
- `ix_user_progress_id` on user_progress(id)

## Foreign Key Constraints
- `user_journeys.user_id` → `users.id`
- `user_journeys.assessment_result_id` → `assessment_results.id`
- `user_lessons.user_id` → `users.id`
- `user_lessons.user_journey_id` → `user_journeys.id`
- `user_lessons.daily_lesson_id` → `daily_lessons.id`
- `user_progress.user_id` → `users.id` (UNIQUE)
- `user_progress.current_journey_id` → `user_journeys.id`

## Migration History
```
4d9e58619a1b (head) - Add user journey system tables
df9c843ee268 - add_assessment_results_table
d546ba715668 - initial_schema
```

## Next Steps

1. **✅ Database Schema**: All tables created successfully
2. **✅ Models**: UserJourney, UserLesson, UserProgress models implemented
3. **✅ Schemas**: Pydantic schemas for API validation
4. **✅ Services**: Business logic services implemented
5. **✅ API Routes**: REST endpoints created
6. **✅ Main App**: Routers registered in FastAPI app

## Ready For:
- Frontend integration
- API testing
- User journey functionality
- Lesson progression system
- Progress tracking

## Testing Commands
```bash
# Check migration status
alembic current

# View migration history
alembic history

# Rollback if needed (NOT RECOMMENDED for production)
alembic downgrade -1

# Apply migration
alembic upgrade head
```

The database is now fully updated and ready to support the complete user journey system!
