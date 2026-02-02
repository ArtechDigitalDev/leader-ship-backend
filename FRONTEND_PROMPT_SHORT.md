# Frontend Prompt: Lesson Commit Timeline Feature

## Task
Implement a "Commit Timeline" feature where users can commit to complete a lesson within X days BEFORE actually completing it. @src/pages/manager/LessonContent.tsx:451-457 ActionCheckInDialog ta remove korar dokar nai. eta etar motoi thak. etar upore etar mothoi arekta component create koro.

## API Endpoint
**POST** `/user-lessons/{lesson_id}/commit`

**Request:**
```json
{
  "commit_by_days": 7,        // Required: Any positive integer (≥1)
  "commit_text": "Optional text"  // Optional: String
}
```

**Response:** {
    "success": true,
    "message": "Commit saved successfully",
    "data": {
        "status": "available",
        "points_earned": 0,
        "commit_text": "hi hello.",
        "commit_by_days": 7,
        "days_between_lessons": 1,
        "id": 288,
        "user_id": 78,
        "user_journey_id": 49,
        "daily_lesson_id": 8,
        "unlocked_at": null,
        "started_at": null,
        "completed_at": null,
        "created_at": "2026-02-02T03:57:22.318811Z",
        "updated_at": "2026-02-02T06:23:06.328985Z"
    },
    "meta": null
}

## UI Requirements

1. same to same @src/pages/manager/LessonContent.tsx:394-448 er moto hobe. but  "commit_by_days" er upor base kore visible hobe. null takle visible hobe

2. **Create new modal/popup** with (ActionCheckInDialog etar kono poriborton korba na):
   After clicking Commit, show a new popup/modal asking:
 “By when will you complete this action?”


Timeline will be restricted via dropdown (not free-form).


Proposed options (finalized verbally):
5 days


7 days


10 days


14 days

   - Buttons: Cancel, Save Commit 
(ActionCheckInDialog er motoi hobe)

3. **Display commit status** after saving:
   - Show: "Committed to complete within {X} days"
   - Show target date: Today + X days
   - Show commit text if provided

4. **Keep Complete separate:** @src/pages/manager/LessonContent.tsx:393-448 
## Key Points
- Commit happens BEFORE completion (separate flows)
- `commit_by_days` can be number
- `commit_text` is optional
- Initial state: both fields are `null`
- After commit: values persist even after lesson completion
