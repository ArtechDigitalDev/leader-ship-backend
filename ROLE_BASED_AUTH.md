# Role-Based Authentication System

This document provides comprehensive documentation for the role-based authentication system with Participant, Coach, and Admin roles.

## Overview

The system implements industry-standard authentication practices with three distinct user roles:
- **Participant**: Regular users taking assessments
- **Coach**: Users who can guide and mentor participants  
- **Admin**: System administrators with full access

## User Roles

### Participant (Default Role)
- Can take assessments and view their results
- Must verify email before login
- Access to profile determination and learning tracks
- Cannot access admin functions

### Coach
- Can view participant progress and results
- Access to coaching tools and analytics
- Can create and manage learning plans
- Cannot access admin functions

### Admin
- Full system access including admin panel
- Can manage all users and system settings
- Access to all analytics and reports
- Can create other admins

## Authentication Flow

### 1. User Registration/Signup

**Endpoint**: `POST /api/v1/auth/signup`

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "mobile_number": "1234567890",
  "password": "password123",
  "role": "participant",  // "participant", "coach", or "admin"
  "terms_accepted": true
}
```

**Response**:
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "role": "participant",
    "is_email_verified": false,
    "is_active": true
  },
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

**Important Notes**:
- New users are created with `is_email_verified: false`
- Email verification is required for non-admin users
- Role defaults to "participant" if not specified
- Password must be minimum 8 characters

### 2. Email Verification

**Step 1 - Request Verification Email**:
```bash
POST /api/v1/auth/resend-verification
{
  "email": "user@example.com"
}
```

**Step 2 - Verify Email**:
```bash
POST /api/v1/auth/verify-email
{
  "token": "verification_token_from_email"
}
```

### 3. Role-Based Login

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "participant"  // Optional: validates user has this role
}
```

**Response**:
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "participant",
    "is_email_verified": true
  },
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

**Role Validation**:
- If `role` is specified, user must have that exact role
- If `role` is not specified, any role can login
- Admin users can login without email verification
- Non-admin users must have verified email

### 4. Password Reset Flow

**Step 1 - Request Password Reset**:
```bash
POST /api/v1/auth/forgot-password
{
  "email": "user@example.com"
}
```

**Step 2 - Reset Password**:
```bash
POST /api/v1/auth/reset-password
{
  "token": "reset_token_from_email",
  "new_password": "newpassword123"
}
```

## Standard Authentication Procedures

### Industry Best Practices Implemented

1. **Password Security**:
   - Minimum 8 characters required
   - Passwords hashed with bcrypt
   - No password storage in plain text

2. **Email Verification**:
   - Required for all non-admin users
   - Prevents fake accounts
   - Token-based verification with expiration

3. **Role-Based Access Control (RBAC)**:
   - Three distinct roles with different permissions
   - Role validation during login
   - Admin-only endpoints protected

4. **JWT Token Security**:
   - Short-lived access tokens (30 minutes default)
   - Secure token generation and validation
   - Token-based password reset and email verification

5. **Account Security**:
   - Email verification required
   - Password reset functionality
   - Account activation/deactivation

### Login Page Integration

The login page should handle:

1. **Role Selection**: 
   - Participant (default)
   - Coach  
   - Admin

2. **Form Fields**:
   - Email address
   - Password
   - Remember me checkbox
   - Forgot password link

3. **Error Handling**:
   - Invalid credentials
   - Unverified email
   - Wrong role selection
   - Account inactive

4. **Success Flow**:
   - Redirect based on role
   - Store JWT token
   - Set user context

## API Endpoints Summary

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/signup` | POST | Register new user | No |
| `/auth/login` | POST | Role-based login | No |
| `/auth/forgot-password` | POST | Request password reset | No |
| `/auth/reset-password` | POST | Reset password with token | No |
| `/auth/verify-email` | POST | Verify email address | No |
| `/auth/resend-verification` | POST | Resend verification email | No |
| `/auth/me` | GET | Get current user info | Yes |

## Frontend Integration Examples

### Login Form
```javascript
const login = async (email, password, role) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, role })
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    // Redirect based on role
    redirectBasedOnRole(data.user.role);
  }
};
```

### Role-Based Redirects
```javascript
const redirectBasedOnRole = (role) => {
  switch (role) {
    case 'participant':
      window.location.href = '/dashboard';
      break;
    case 'coach':
      window.location.href = '/coach-dashboard';
      break;
    case 'admin':
      window.location.href = '/admin-panel';
      break;
  }
};
```

### Protected Routes
```javascript
const requireRole = (requiredRole) => {
  const token = localStorage.getItem('token');
  const user = getCurrentUser(); // Decode JWT
  
  if (!user || user.role !== requiredRole) {
    window.location.href = '/login';
  }
};
```

## Security Considerations

1. **Production Deployment**:
   - Remove token exposure in API responses
   - Implement proper email sending service
   - Use HTTPS for all communications
   - Set secure JWT secret

2. **Rate Limiting**:
   - Implement rate limiting on login attempts
   - Limit password reset requests
   - Prevent brute force attacks

3. **Session Management**:
   - Short token expiration times
   - Implement refresh token mechanism
   - Proper logout functionality

4. **Data Protection**:
   - Encrypt sensitive data
   - Implement audit logging
   - Regular security updates

## Error Codes and Messages

| Error | Status | Message |
|-------|--------|---------|
| Invalid credentials | 401 | "Incorrect email or password" |
| Unverified email | 400 | "Please verify your email address before logging in" |
| Wrong role | 403 | "Access denied. Expected role: X, but user has role: Y" |
| Inactive account | 400 | "Inactive user" |
| Invalid token | 400 | "Invalid or expired token" |
| Email exists | 400 | "A user with this email already exists" |

This authentication system provides a robust, secure, and scalable foundation for the leadership development platform with proper role-based access control.
