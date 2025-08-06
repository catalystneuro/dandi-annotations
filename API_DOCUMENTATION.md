# DANDI External Resources REST API Documentation

## Overview

The DANDI External Resources REST API provides programmatic access to all functionality of the DANDI annotation web application. This API enables automated submissions, data retrieval, and integration with external systems.

**Base URL:** `http://localhost:5000/api`

**Content Type:** All POST/PUT requests must use `Content-Type: application/json`

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message",
  "pagination": { ... }  // Only for paginated endpoints
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }  // Optional additional details
  }
}
```

### Pagination Format
```json
{
  "page": 1,
  "per_page": 10,
  "total_items": 25,
  "total_pages": 3,
  "has_prev": false,
  "has_next": true,
  "prev_page": null,
  "next_page": 2,
  "start_item": 1,
  "end_item": 10
}
```

## Authentication

The API uses session-based authentication. Some endpoints require authentication or moderator privileges.

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "User Name",
    "email": "user@example.com",
    "user_type": "user"
  },
  "message": "Login successful"
}
```

### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "confirm_password": "securepassword123"
}
```

### Get Current User
```http
GET /api/auth/me
```
*Requires authentication*

### Logout
```http
POST /api/auth/logout
```

## Dandiset Endpoints

### List All Dandisets
```http
GET /api/dandisets?page=1&per_page=10
```

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "dandiset_id": "dandiset_000001",
      "display_id": "DANDI:000001",
      "approved_count": 5,
      "community_count": 2,
      "total_count": 7
    }
  ],
  "pagination": { ... }
}
```

### Get Specific Dandiset
```http
GET /api/dandisets/dandiset_000001
```

**Response:**
```json
{
  "success": true,
  "data": {
    "dandiset_id": "dandiset_000001",
    "display_id": "DANDI:000001",
    "approved_count": 5,
    "community_count": 2,
    "total_count": 7
  }
}
```

### Get Dandiset Resources
```http
GET /api/dandisets/dandiset_000001/resources?page=1&per_page=10
```

Returns both approved and pending resources (pending only visible to authenticated users).

### Get Approved Resources Only
```http
GET /api/dandisets/dandiset_000001/resources/approved?page=1&per_page=10
```

### Get Pending Resources
```http
GET /api/dandisets/dandiset_000001/resources/pending?page=1&per_page=10
```
*Requires authentication*

## Resource Submission

### Submit New Resource
```http
POST /api/dandisets/dandiset_000001/resources
Content-Type: application/json

{
  "resource_name": "Analysis Code Repository",
  "resource_url": "https://github.com/user/analysis-code",
  "repository": "GitHub",
  "relation": "IsSupplementTo",
  "resource_type": "Software",
  "contributor_name": "John Doe",
  "contributor_email": "john@example.com",
  "contributor_identifier": "https://orcid.org/0000-0000-0000-0000",
  "contributor_url": "https://johndoe.com",
  "resource_identifier": "optional-resource-id"
}
```

**Required Fields:**
- `resource_name`: Name of the resource
- `resource_url`: Valid HTTP/HTTPS URL
- `repository`: Repository type (e.g., "GitHub", "Zenodo", "Figshare")
- `relation`: Relationship to dandiset (e.g., "IsSupplementTo", "IsReferencedBy")
- `resource_type`: Type of resource (e.g., "Software", "Dataset", "Publication")
- `contributor_name`: Name of the contributor
- `contributor_email`: Valid email address

**Optional Fields:**
- `contributor_identifier`: ORCID URL
- `contributor_url`: Contributor's website
- `resource_identifier`: Additional resource identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "dandiset_id": "dandiset_000001",
    "name": "Analysis Code Repository",
    "url": "https://github.com/user/analysis-code",
    "repository": "GitHub",
    "relation": "IsSupplementTo",
    "resource_type": "Software",
    "annotation_contributor": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "filename": "new_submission.yaml",
    "status": "pending"
  },
  "message": "Resource submitted successfully for review"
}
```

### Get Specific Resource
```http
GET /api/resources/resource_id_123
```

## Moderation Endpoints

### Get All Pending Submissions
```http
GET /api/submissions/pending?page=1&per_page=10
```
*Requires moderator privileges*

### Approve Submission
```http
POST /api/submissions/dandiset_000001/submission_file.yaml/approve
Content-Type: application/json

{
  "moderator_name": "Moderator Name",
  "moderator_email": "moderator@example.com",
  "moderator_identifier": "https://orcid.org/0000-0000-0000-0000",
  "moderator_url": "https://moderator.com"
}
```
*Requires moderator privileges*

**Required Fields:**
- `moderator_name`: Name of the moderator
- `moderator_email`: Valid email address

### Delete Submission
```http
DELETE /api/submissions/dandiset_000001/submission_file.yaml/delete?status=community
Content-Type: application/json

{
  "moderator_name": "Moderator Name",
  "moderator_email": "moderator@example.com",
  "moderator_identifier": "https://orcid.org/0000-0000-0000-0000",
  "moderator_url": "https://moderator.com"
}
```
*Requires moderator privileges*

**Required Fields:**
- `moderator_name`: Name of the moderator
- `moderator_email`: Valid email address

**Query Parameters:**
- `status`: Must be either "community" or "approved"

**Response:**
```json
{
  "success": true,
  "data": {
    "dandiset_id": "dandiset_000001",
    "filename": "submission_file.yaml",
    "status": "community",
    "resource_name": "Resource Name",
    "deleted_by": "Moderator Name",
    "deletion_date": "2025-01-04T10:30:00.000Z"
  },
  "message": "Submission 'Resource Name' deleted successfully"
}
```

### Delete Resource by ID
```http
DELETE /api/resources/resource_id_123
Content-Type: application/json

{
  "moderator_name": "Moderator Name",
  "moderator_email": "moderator@example.com",
  "moderator_identifier": "https://orcid.org/0000-0000-0000-0000",
  "moderator_url": "https://moderator.com"
}
```
*Requires moderator privileges*

**Required Fields:**
- `moderator_name`: Name of the moderator
- `moderator_email`: Valid email address

**Response:**
```json
{
  "success": true,
  "data": {
    "resource_id": "resource_id_123",
    "dandiset_id": "dandiset_000001",
    "filename": "submission_file.yaml",
    "status": "community",
    "resource_name": "Resource Name",
    "deleted_by": "Moderator Name",
    "deletion_date": "2025-01-04T10:30:00.000Z"
  },
  "message": "Resource 'Resource Name' deleted successfully"
}
```

### Get User Submissions
```http
GET /api/submissions/user/user@example.com?community_page=1&approved_page=1&per_page=10
```
*Requires authentication (users can only view their own submissions unless they're moderators)*

**Response:**
```json
{
  "success": true,
  "data": {
    "community_submissions": [ ... ],
    "approved_submissions": [ ... ],
    "community_pagination": { ... },
    "approved_pagination": { ... }
  }
}
```

## Statistics Endpoints

### Platform Overview Statistics
```http
GET /api/stats/overview
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_dandisets": 150,
    "total_approved_resources": 342,
    "total_pending_resources": 28,
    "total_resources": 370,
    "unique_contributors": 89,
    "dandisets_with_resources": 127
  }
}
```

### Dandiset-Specific Statistics
```http
GET /api/stats/dandisets/dandiset_000001
```

**Response:**
```json
{
  "success": true,
  "data": {
    "dandiset_id": "dandiset_000001",
    "display_id": "DANDI:000001",
    "approved_count": 5,
    "pending_count": 2,
    "total_count": 7,
    "unique_contributors": 4,
    "resource_types": {
      "Software": 3,
      "Dataset": 2,
      "Publication": 2
    },
    "repositories": {
      "GitHub": 3,
      "Zenodo": 2,
      "Figshare": 2
    }
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `INVALID_CREDENTIALS` | Authentication failed |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient privileges |
| `NOT_FOUND` | Resource not found |
| `METHOD_NOT_ALLOWED` | HTTP method not allowed |
| `EMAIL_EXISTS` | Email already registered |
| `APPROVAL_FAILED` | Submission approval failed |
| `INTERNAL_ERROR` | Server error |

## Usage Examples

### Automated Submission Script (Python)
```python
import requests
import json

# Configuration
API_BASE = "http://localhost:5000/api"
DANDISET_ID = "dandiset_000001"

# Resource data
resource_data = {
    "resource_name": "Automated Analysis Pipeline",
    "resource_url": "https://github.com/lab/analysis-pipeline",
    "repository": "GitHub",
    "relation": "IsSupplementTo",
    "resource_type": "Software",
    "contributor_name": "Analysis Bot",
    "contributor_email": "bot@lab.edu"
}

# Submit resource
response = requests.post(
    f"{API_BASE}/dandisets/{DANDISET_ID}/resources",
    headers={"Content-Type": "application/json"},
    data=json.dumps(resource_data)
)

if response.status_code == 201:
    result = response.json()
    print(f"Successfully submitted: {result['data']['name']}")
    print(f"Status: {result['data']['status']}")
else:
    error = response.json()
    print(f"Error: {error['error']['message']}")
```

### Fetch Dandiset Resources (JavaScript)
```javascript
async function fetchDandisetResources(dandisetId) {
    try {
        const response = await fetch(`/api/dandisets/${dandisetId}/resources`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`Found ${data.data.length} resources`);
            data.data.forEach(resource => {
                console.log(`- ${resource.name}: ${resource.url}`);
            });
        } else {
            console.error('Error:', data.error.message);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}

// Usage
fetchDandisetResources('dandiset_000001');
```

### Bulk Approval Script (Python)
```python
import requests
import json

# Login as moderator
login_data = {
    "username": "moderator@example.com",
    "password": "moderator_password"
}

session = requests.Session()
login_response = session.post(
    f"{API_BASE}/auth/login",
    headers={"Content-Type": "application/json"},
    data=json.dumps(login_data)
)

if login_response.status_code == 200:
    # Get pending submissions
    pending_response = session.get(f"{API_BASE}/submissions/pending")
    pending_data = pending_response.json()
    
    # Approve each submission
    for submission in pending_data['data']:
        approval_data = {
            "moderator_name": "Auto Moderator",
            "moderator_email": "moderator@example.com"
        }
        
        approve_response = session.post(
            f"{API_BASE}/submissions/{submission['dandiset_id']}/{submission['filename']}/approve",
            headers={"Content-Type": "application/json"},
            data=json.dumps(approval_data)
        )
        
        if approve_response.status_code == 200:
            print(f"Approved: {submission['name']}")
        else:
            print(f"Failed to approve: {submission['name']}")
```

## Rate Limiting

Currently, no rate limiting is implemented, but it's recommended to:
- Limit requests to 100 per minute per IP
- Use pagination for large datasets
- Implement exponential backoff for failed requests

## Versioning

The current API version is v1. Future versions will be accessible via `/api/v2/` etc.

## Support

For API support and questions:
- Check the error response for specific error codes and messages
- Ensure all required fields are provided
- Validate email addresses and URLs before submission
- Use proper authentication for protected endpoints

## Changelog

### v1.0.0 (2025-01-04)
- Initial API release
- All core endpoints implemented
- Authentication and authorization
- Comprehensive error handling
- Pagination support
