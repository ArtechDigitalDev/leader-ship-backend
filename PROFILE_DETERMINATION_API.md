# Profile Determination API Usage Examples

This document provides examples of how to use the new profile determination endpoints.

## New Endpoints

### 1. Profile Determination Only
**POST** `/assessments/5cs/profile-determination`

Returns detailed leadership profile information based on assessment responses.

### 2. Complete Profile Assessment
**POST** `/assessments/5cs/complete-profile`

Returns both traditional 5Cs assessment results AND detailed profile determination.

## Example Usage

### Sample Request Body
```json
{
  "responses": [4, 5, 3, 4, 5, 2, 3, 4, 3, 2, 5, 4, 5, 4, 5, 3, 2, 4, 3, 2, 4, 5, 3, 4, 5]
}
```

### Sample Response (Profile Determination)
```json
{
  "leadership_profile": {
    "primary_type": "COLLABORATIVE LEADER",
    "description": "You excel at bringing people together and building consensus. Your strength lies in creating inclusive environments.",
    "strengths": [
      "Team building & relationship management",
      "Active listening & empathy",
      "Conflict resolution",
      "Inclusive decision making"
    ],
    "areas_for_development": [
      "Decisive leadership in crisis",
      "Setting firm boundaries",
      "Time management & prioritization",
      "Difficult conversations"
    ],
    "learning_tracks": [
      {
        "title": "BOUNDARY SETTING",
        "description": "Learn to set clear expectations while preserving relationships",
        "is_recommended": true
      },
      {
        "title": "DECISIVE LEADERSHIP",
        "description": "Build confidence in making tough decisions quickly and effectively",
        "is_recommended": false
      },
      {
        "title": "DIFFICULT CONVERSATIONS",
        "description": "Master challenging discussions with confidence and clarity",
        "is_recommended": false
      }
    ],
    "profile_content": {
      "growth_focus_summary": "You're currently navigating leadership without a clear anchor. You may feel pulled in multiple directions, often reacting to urgent needs while struggling to prioritize what truly matters. This can lead to decision fatigue and a lack of long-term direction for your team.",
      "intentional_advantage_summary": "You lead with relational strength—creating safe spaces where others feel seen, heard, and valued. Your challenge now is to use that connection as a force for growth and accountability."
    }
  },
  "category_scores": {
    "clarity": 21,
    "consistency": 14,
    "connection": 23,
    "courage": 14,
    "curiosity": 21
  },
  "growth_focus": "consistency",
  "intentional_advantage": "connection",
  "is_balanced_leader": false
}
```

## Leadership Types

The system determines one of six leadership types based on the highest scoring category:

1. **VISIONARY LEADER** (Clarity highest)
2. **STEADY LEADER** (Consistency highest)
3. **COLLABORATIVE LEADER** (Connection highest)
4. **BOLD LEADER** (Courage highest)
5. **INNOVATIVE LEADER** (Curiosity highest)
6. **INTEGRATED LEADER** (Balanced across all categories)

## Learning Tracks

Each leadership type has three learning tracks, with one recommended based on the growth focus area:

- **STRATEGIC VISION**: Develop skills in long-term planning and purpose-driven leadership
- **SYSTEMS BUILDING**: Create sustainable processes and reliable leadership habits
- **BOUNDARY SETTING**: Learn to set clear expectations while preserving relationships
- **DECISIVE LEADERSHIP**: Build confidence in making tough decisions quickly and effectively
- **DIFFICULT CONVERSATIONS**: Master challenging discussions with confidence and clarity
- **MENTORING MASTERY**: Develop advanced skills in developing and scaling others
- **ORGANIZATIONAL TRANSFORMATION**: Lead large-scale change and cultural evolution
- **PURPOSE EXPLORATION**: Deepen your understanding of personal and organizational purpose

## Integration Notes

- The profile determination uses the same 25-question 5Cs assessment
- Responses should be integers from 1-5 (Likert scale)
- Questions 1-5: Clarity, 6-10: Consistency, 11-15: Connection, 16-20: Courage, 21-25: Curiosity
- Balanced leaders have scores within 3 points of each other across all categories
