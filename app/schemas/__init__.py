# Pydantic schemas for request/response models

from .daily_lesson import (
    DailyTip,
    SwipeCard,
    Choice,
    Scenario,
    GoDeeper,
    DailyLessonBase,
    DailyLessonCreate,
    DailyLessonUpdate,
    DailyLessonResponse
)

from .user_journey import (
    UserJourneyBase,
    UserJourneyCreate,
    UserJourneyUpdate,
    UserJourney,
    UserJourneyWithProgress,
    UserJourneyStartRequest
)

from .user_lesson import (
    UserLessonBase,
    UserLessonCreate,
    UserLessonUpdate,
    UserLesson,
    UserLessonWithDetails,
    LessonCompletionRequest,
    LessonUnlockRequest
)

from .user_progress import (
    UserProgressBase,
    UserProgressCreate,
    UserProgressUpdate,
    UserProgress,
    UserProgressWithStats,
    ProgressUpdateRequest
)

from .user_preferences import (
    UserPreferencesBase,
    UserPreferencesResponse,
    UserPreferencesUpdate
)