# Admin Panel API Documentation

This document provides comprehensive documentation for the Admin Panel API endpoints.

## Overview

The Admin Panel provides comprehensive user management capabilities including:
- User statistics and analytics
- User search and filtering
- User CRUD operations
- Bulk user actions
- Data export functionality

## Authentication

All admin endpoints require:
1. **Authentication**: Valid JWT token
2. **Authorization**: User must have `is_superuser=True`

## Endpoints

### Dashboard & Statistics

#### Get Admin Dashboard
**GET** `/api/v1/admin/dashboard`

Returns comprehensive dashboard statistics including user stats, assessment stats, recent users, and top performing users.

**Response:**
```json
{
  "user_stats": {
    "total_users": 47,
    "active_users": 39,
    "pending_users": 5,
    "inactive_users": 3
  },
  "assessment_stats": {
    "total_assessments": 120,
    "completed_assessments": 95,
    "average_score": 78.5,
    "most_common_profile": "Collaborative Leader"
  },
  "recent_users": [...],
  "top_performing_users": [...]
}
```

#### Get User Statistics
**GET** `/api/v1/admin/users/stats`

Returns user statistics only.

### User Management

#### List Users
**GET** `/api/v1/admin/users`

Get paginated list of users with search and filter capabilities.

**Query Parameters:**
- `query` (string): Search by name, email, or username
- `status` (string): Filter by status (`active`, `inactive`, `pending`)
- `learning_track` (string): Filter by learning track
- `page` (int): Page number (default: 1)
- `per_page` (int): Users per page (default: 10, max: 100)

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "username": "user1",
      "full_name": "John Doe",
      "mobile_number": "1234567890",
      "is_active": true,
      "is_superuser": false,
      "learning_track": "Strategic Vision",
      "assessment_count": 3,
      "last_assessment_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 10,
  "total_pages": 5
}
```

#### Create User
**POST** `/api/v1/admin/users`

Create a new user.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "full_name": "New User",
  "mobile_number": "1234567890",
  "password": "password123",
  "is_active": true,
  "is_superuser": false,
  "learning_track": "Strategic Vision"
}
```

#### Get User Details
**GET** `/api/v1/admin/users/{user_id}`

Get detailed information about a specific user.

#### Update User
**PUT** `/api/v1/admin/users/{user_id}`

Update user information.

**Request Body:**
```json
{
  "full_name": "Updated Name",
  "is_active": true,
  "learning_track": "Strategic Vision"
}
```

#### Delete User
**DELETE** `/api/v1/admin/users/{user_id}`

Delete a user permanently.

### Bulk Operations

#### Bulk User Action
**POST** `/api/v1/admin/users/bulk-action`

Perform bulk actions on multiple users.

**Request Body:**
```json
{
  "user_ids": [1, 2, 3],
  "action": "activate"  // "activate", "deactivate", or "delete"
}
```

**Response:**
```json
{
  "message": "Bulk action 'activate' completed successfully",
  "affected_users": 3
}
```

### Data Export

#### Export Users
**POST** `/api/v1/admin/users/export`

Export user data in CSV or JSON format.

**Request Body:**
```json
{
  "format": "csv",  // "csv" or "json"
  "include_inactive": false,
  "include_assessments": true
}
```

**Response:** File download (CSV or JSON)

## User Status Definitions

- **Active**: Users with `is_active=True`
- **Inactive**: Users with `is_active=False`
- **Pending**: Active users who haven't completed any assessments

## Learning Tracks

The system tracks learning tracks based on assessment results:
- Strategic Vision
- Systems Building
- Boundary Setting
- Decisive Leadership
- Difficult Conversations
- Mentoring Mastery
- Organizational Transformation
- Purpose Exploration

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin privileges required"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 400 Bad Request
```json
{
  "detail": "User with this email or username already exists"
}
```

## Usage Examples

### Get Dashboard Stats
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/v1/admin/dashboard
```

### Search Users
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8001/api/v1/admin/users?query=john&status=active&page=1&per_page=20"
```

### Create User
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","full_name":"User Name","mobile_number":"1234567890","password":"password123","is_active":true}' \
  http://localhost:8001/api/v1/admin/users
```

### Export Users
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"format":"csv","include_assessments":true}' \
  http://localhost:8001/api/v1/admin/users/export \
  --output users_export.csv
```

## Security Notes

1. All admin endpoints require superuser privileges
2. User passwords are hashed using bcrypt
3. Sensitive operations (delete, bulk actions) should be logged
4. Export functionality should be rate-limited in production
5. Consider implementing audit logs for admin actions

## Integration with Frontend

The admin panel endpoints are designed to work seamlessly with the admin interface shown in the image:

- **Dashboard Cards**: Use `/admin/dashboard` endpoint
- **User List Table**: Use `/admin/users` with search/filter parameters
- **User Actions**: Use individual CRUD endpoints
- **Export Button**: Use `/admin/users/export` endpoint
- **Bulk Actions**: Use `/admin/users/bulk-action` endpoint

## Rate Limiting

Consider implementing rate limiting for:
- Export operations (prevent abuse)
- Bulk actions (prevent system overload)
- Search operations (prevent excessive queries)
