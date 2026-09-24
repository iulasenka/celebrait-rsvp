# JWT Authentication & User Context Implementation Summary

## Overview
Successfully implemented JWT-based authentication and user context for the RSVP application, replacing the previous bearer email pattern with proper JWT tokens.

## Changes Made

### 1. Authentication & Security
- **New JWT Module** (`app/auth.py`):
  - HS256 algorithm with 30-minute token expiration
  - JWT secret key: `ab68f77d1f0d5b46bfdf7a45f18cc04e7b91478a4eaef7e7d85c108a70f6b6ef`
  - Functions: `create_jwt_token()`, `decode_jwt_token()`, `get_current_user()`
  - JWT sub field contains opaque user_id string

### 2. Data Model Updates
- **Invitation Model**:
  - Added `user_id: str` field (from JWT sub)
  - Added `deleted_at: datetime | None` field for soft deletion
  - Kept `owner_email` as information field (from request body)

### 3. Database Schema
- **SQLite Schema Updates**:
  - Added `user_id TEXT NOT NULL` column to invitations table
  - Added `deleted_at TEXT` column to invitations table
  - Added index on `user_id` for performance
  - Created `migrate_db.py` script for existing database migration

### 4. Authorization Rules
- **Public Endpoints** (no authentication required):
  - `GET /v1/invitations/{id}` - View invitation details
  - `POST /v1/invitations/{id}/responses` - Submit RSVP
  - `GET /v1/invitations/{id}/responses/{manage_token}` - Retrieve response via token
  - `PATCH /v1/invitations/{id}/responses/{manage_token}` - Update response via token

- **Authenticated Endpoints** (require JWT):
  - `POST /v1/invitations` - Create invitation (uses JWT user_id)
  - `GET /v1/invitations` - List user's invitations
  - `PATCH /v1/invitations/{id}` - Update invitation (owner check)
  - `DELETE /v1/invitations/{id}` - Soft delete invitation (new endpoint)
  - `GET /v1/invitations/{id}/responses` - List responses (owner check)

### 5. HTTP Status Codes
- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: 
  - User tries to modify another user's invitation
  - Invalid manage_token for response access
- **404 Not Found**:
  - Invitation/response doesn't exist
  - Accessing deleted invitation/response

### 6. Service Layer Updates
- All CRUD operations now require `user_id` parameter
- Authorization checks before modification operations
- Soft deletion: sets `deleted_at` timestamp instead of physical deletion
- Deleted invitations filtered from lists and API responses
- Separate public access method: `get_invitation_for_guest()`

### 7. Tests
- **Service Tests** (`tests/test_service.py`):
  - User isolation tests
  - Soft deletion tests
  - Authorization enforcement tests
  
- **API Integration Tests** (`tests/test_api.py`):
  - JWT authentication tests
  - Public endpoint access tests
  - Authorization failure tests (401, 403, 404)
  - User isolation tests
  - Deleted invitation handling

### 8. Dependencies
- Added `pyjwt>=2.8,<3.0` to pyproject.toml
- Updated pyproject.toml with build system configuration

## Migration Guide

For existing databases, run:
```bash
python migrate_db.py [database_path]
```

This will:
1. Add `user_id` column (default: `legacy-user-{owner_email}`)
2. Add `deleted_at` column
3. Create necessary indexes

## Testing Token Creation (for external service)

```python
from app.auth import create_jwt_token

# Create a token for a user
user_token = create_jwt_token("user-unique-id-from-external-service")

# Use in API requests
headers = {"Authorization": f"Bearer {user_token}"}
```

## Security Notes
- JWT secret is hardcoded temporarily (as per requirements)
- Tokens expire after 30 minutes
- External service is responsible for user authentication and token issuance
- Tests construct tokens directly using `create_jwt_token()`

## All Requirements Implemented ✓
1. ✓ User context added to API calls via JWT sub
2. ✓ Invitation model includes user_id
3. ✓ Owner email kept as information field
4. ✓ JWT replaces bearer email pattern
5. ✓ Authorization guards on endpoints
6. ✓ Public endpoints available to unauthenticated guests
7. ✓ Authenticated users can CRUD their invitations
8. ✓ DELETE endpoint with soft deletion
9. ✓ Proper HTTP status codes (401, 403, 404)
10. ✓ HS256 algorithm with 30-minute expiration
11. ✓ Unit tests for authorization
