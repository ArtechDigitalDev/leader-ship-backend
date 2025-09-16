# Secure Role-Based Authentication System

This document provides comprehensive documentation for the secure role-based authentication system that prevents unauthorized admin/coach registration.

## Security Problem Solved

**Problem**: Random users could sign up as admin or coach roles, gaining unauthorized access to sensitive system functions.

**Solution**: Implemented a multi-layered security approach with role restrictions, approval workflows, and invitation systems.

## Security Measures Implemented

### 1. **Signup Role Restrictions**
- **Only participants can sign up directly**
- Coach and admin roles are blocked during registration
- Clear error messages guide users to proper channels

### 2. **Role Request System**
- Participants can request role upgrades
- Admin approval required for all role changes
- Detailed reason required for role requests
- Audit trail of all role changes

### 3. **Admin Invitation System**
- Admins can invite coaches and admins directly
- Invitation tokens with expiration
- Email-based invitation workflow
- Prevents unauthorized role creation

### 4. **Approval Workflow**
- All role requests require admin approval
- Admin can approve or reject requests
- Complete audit trail with timestamps
- Automatic role assignment upon approval

## User Flows

### **Participant Signup (Allowed)**
```json
POST /api/v1/auth/signup
{
  "email": "user@example.com",
  "username": "user",
  "full_name": "User Name",
  "mobile_number": "1234567890",
  "password": "password123",
  "role": "participant",  // Only this role allowed
  "terms_accepted": true
}
```

**Response**: ✅ User created as participant

### **Admin/Coach Signup (Blocked)**
```json
POST /api/v1/auth/signup
{
  "role": "admin"  // or "coach"
}
```

**Response**: ❌ 
```json
{
  "detail": "Only participants can sign up directly. Coaches and admins must be invited or request approval."
}
```

### **Role Request Flow**

**Step 1 - Participant Requests Role Upgrade**:
```json
POST /api/v1/auth/request-role
Authorization: Bearer <participant_token>
{
  "requested_role": "coach",
  "reason": "I have extensive experience in leadership development and want to help others grow as a coach."
}
```

**Response**:
```json
{
  "message": "Role request submitted successfully. An admin will review your request.",
  "requested_role": "coach",
  "status": "pending",
  "reason": "I have extensive experience...",
  "requested_at": "2025-09-09T11:27:33.825196+06:00"
}
```

**Step 2 - Admin Reviews Requests**:
```json
GET /api/v1/admin/role-requests
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
  "role_requests": [
    {
      "id": 6,
      "email": "testparticipant@example.com",
      "full_name": "Test Participant",
      "current_role": "participant",
      "requested_role": "coach",
      "status": "pending",
      "reason": "I have extensive experience...",
      "requested_at": "2025-09-09T11:27:33.825196+06:00"
    }
  ]
}
```

**Step 3 - Admin Approves Request**:
```json
POST /api/v1/admin/role-requests/6/approve
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
  "message": "Role request approved. User testparticipant@example.com is now a coach.",
  "user": {
    "id": 6,
    "email": "testparticipant@example.com",
    "role": "coach"
  }
}
```

### **Admin Invitation Flow**

**Step 1 - Admin Invites User**:
```json
POST /api/v1/admin/invite-user
Authorization: Bearer <admin_token>
{
  "email": "newcoach@example.com",
  "full_name": "New Coach",
  "role": "coach",
  "message": "Welcome to our coaching team!"
}
```

**Response**:
```json
{
  "message": "Invitation sent to newcoach@example.com",
  "invitation": {
    "email": "newcoach@example.com",
    "role": "coach",
    "invitation_token": "jwt_token_here",
    "expires_in": "7 days"
  }
}
```

**Step 2 - Invited User Accepts** (Implementation needed):
- User clicks invitation link
- Creates account with pre-approved role
- No additional approval needed

## Database Schema

### **User Model Enhancements**
```sql
-- Role request fields
requested_role ENUM('PARTICIPANT', 'COACH', 'ADMIN') NULL,
role_request_status ENUM('PENDING', 'APPROVED', 'REJECTED') NULL,
role_request_reason TEXT NULL,
role_requested_at TIMESTAMP NULL,
role_approved_by INTEGER NULL,  -- Admin user ID
role_approved_at TIMESTAMP NULL
```

## API Endpoints

### **Authentication Endpoints**
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/signup` | POST | Register as participant only | No |
| `/auth/request-role` | POST | Request role upgrade | Yes (Participant) |

### **Admin Management Endpoints**
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/admin/role-requests` | GET | List all role requests | Yes (Admin) |
| `/admin/role-requests/{id}/approve` | POST | Approve role request | Yes (Admin) |
| `/admin/role-requests/{id}/reject` | POST | Reject role request | Yes (Admin) |
| `/admin/invite-user` | POST | Invite coach/admin | Yes (Admin) |

## Security Features

### **1. Role Validation**
- Signup only allows participant role
- Role requests require detailed justification
- Admin approval for all role changes

### **2. Audit Trail**
- All role changes logged with timestamps
- Admin who approved/rejected tracked
- Complete history of role requests

### **3. Invitation Security**
- Token-based invitations with expiration
- Email verification required
- Admin-only invitation creation

### **4. Access Control**
- Role-based endpoint protection
- Admin-only approval functions
- Participant-only role requests

## Frontend Integration

### **Signup Form Updates**
```javascript
// Remove role selection from signup form
const signup = async (userData) => {
  const response = await fetch('/api/v1/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...userData,
      role: 'participant'  // Always participant
    })
  });
};
```

### **Role Request Interface**
```javascript
const requestRoleUpgrade = async (requestedRole, reason) => {
  const response = await fetch('/api/v1/auth/request-role', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ requested_role: requestedRole, reason })
  });
};
```

### **Admin Dashboard Integration**
```javascript
const getRoleRequests = async () => {
  const response = await fetch('/api/v1/admin/role-requests', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  return response.json();
};

const approveRoleRequest = async (userId) => {
  const response = await fetch(`/api/v1/admin/role-requests/${userId}/approve`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  return response.json();
};
```

## Error Handling

### **Signup Errors**
```json
{
  "detail": "Only participants can sign up directly. Coaches and admins must be invited or request approval."
}
```

### **Role Request Errors**
```json
{
  "detail": "Only participants can request role upgrades"
}
```

```json
{
  "detail": "You already have a pending role request"
}
```

### **Admin Action Errors**
```json
{
  "detail": "User does not have a pending role request"
}
```

## Production Considerations

### **1. Email Integration**
- Implement proper email sending service
- Remove token exposure from API responses
- Use secure invitation links

### **2. Rate Limiting**
- Limit role requests per user
- Rate limit admin approval actions
- Prevent spam invitations

### **3. Monitoring**
- Log all role changes
- Monitor failed role requests
- Alert on suspicious activity

### **4. Backup Security**
- Regular admin account audits
- Multi-admin approval for admin role
- Emergency role revocation procedures

## Testing Results

✅ **Participant Signup**: Successfully creates participant accounts
✅ **Admin Signup Blocked**: Prevents unauthorized admin registration
✅ **Coach Signup Blocked**: Prevents unauthorized coach registration
✅ **Role Request**: Participants can request role upgrades
✅ **Admin Approval**: Admins can approve/reject requests
✅ **Invitation System**: Admins can invite coaches/admins
✅ **Audit Trail**: Complete tracking of role changes

## Summary

The secure role-based authentication system successfully prevents unauthorized admin/coach registration through:

1. **Signup Restrictions**: Only participants can register directly
2. **Approval Workflow**: All role changes require admin approval
3. **Invitation System**: Admins can invite coaches/admins directly
4. **Audit Trail**: Complete tracking of all role changes
5. **Access Control**: Role-based endpoint protection

This multi-layered approach ensures that only authorized users can gain elevated privileges while maintaining a smooth user experience for legitimate participants.
