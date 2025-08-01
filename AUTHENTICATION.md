# DANDI External Resources - Authentication System

## Overview

The DANDI External Resources webapp now includes a unified interface with authentication to control approval permissions. This allows moderators to log in and approve community submissions directly from the main interface.

## Authentication Features

### User Types
- **Anonymous Users**: Can view all resources and submit new resources
- **Authenticated Moderators**: Can view, submit, and approve resources

### Login System
- Simple username/password authentication
- Session-based authentication (24-hour sessions)
- Secure password hashing using bcrypt

## Default Moderator Accounts

For testing and initial setup, the following moderator accounts are available:

| Username | Password | Name | Email |
|----------|----------|------|-------|
| admin | admin123 | Administrator | admin@example.com |
| moderator1 | mod123 | Moderator One | moderator1@example.com |

**⚠️ Important**: Change these default passwords in production!

## Configuration

### Moderator Configuration File
Moderators are configured in `src/dandiannotations/webapp/config/moderators.yaml`:

```yaml
moderators:
  admin:
    username: admin
    password_hash: $2b$12$...  # bcrypt hash
    name: Administrator
    email: admin@example.com
  
  moderator1:
    username: moderator1
    password_hash: $2b$12$...  # bcrypt hash
    name: Moderator One
    email: moderator1@example.com
```

### Adding New Moderators

1. Generate a password hash:
```python
import bcrypt
password_hash = bcrypt.hashpw('your_password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(password_hash)
```

2. Add the new moderator to `moderators.yaml`:
```yaml
  new_moderator:
    username: new_moderator
    password_hash: $2b$12$your_generated_hash
    name: New Moderator Name
    email: moderator@example.com
```

## User Interface Changes

### Navigation
- **Login/Logout**: Available in the top navigation bar
- **User Status**: Shows current user name and email when logged in
- **Moderator Badge**: Authenticated users see a shield icon

### Conditional Features
- **Moderate Button**: Only visible to authenticated moderators
- **Approve Buttons**: Only visible to authenticated moderators on community submissions
- **Moderation Page**: Protected by authentication

### Visual Indicators
- **Moderator Status**: Clear indication when logged in as a moderator
- **Approval Actions**: Prominent "Approve Submission" buttons on community resources
- **Authentication State**: Login/logout options based on current state

## Security Features

- **Password Hashing**: All passwords stored as bcrypt hashes
- **Session Management**: Secure session handling with Flask-Session
- **Route Protection**: Approval actions require authentication
- **CSRF Protection**: Built into Flask's session management

## Usage Workflow

### For Regular Users
1. Visit the homepage
2. Browse approved and community resources
3. Submit new resources (no login required)

### For Moderators
1. Click "Login" in the navigation
2. Enter username and password
3. Browse resources with approval capabilities
4. Click "Approve Submission" on community resources
5. Fill out approval form (pre-populated with moderator info)
6. Submit approval to move resource to approved folder

## File Structure

```
src/dandiannotations/webapp/
├── config/
│   └── moderators.yaml          # Moderator credentials
├── utils/
│   └── auth.py                  # Authentication manager
├── templates/
│   ├── login.html              # Login form
│   ├── base.html               # Updated with auth navigation
│   └── ...                     # Other templates updated for auth
└── app.py                      # Main app with auth integration
```

## Development Notes

- Sessions are stored in the filesystem (Flask-Session default)
- Session lifetime is 24 hours
- Authentication state is available to all templates via context processor
- Login redirects preserve the intended destination page

## Production Considerations

1. **Change Default Passwords**: Update all default moderator passwords
2. **Secret Key**: Change the Flask secret key from the default
3. **Session Storage**: Consider Redis or database for session storage in production
4. **HTTPS**: Ensure the application runs over HTTPS in production
5. **Password Policy**: Implement stronger password requirements
6. **Rate Limiting**: Add rate limiting for login attempts

## Troubleshooting

### Common Issues

1. **Login Fails**: Check that the password hash in `moderators.yaml` is correct
2. **Session Expires**: Sessions last 24 hours; users need to log in again
3. **Permissions**: Ensure the webapp can read/write to the session directory
4. **Dependencies**: Make sure `bcrypt` and `flask-session` are installed

### Regenerating Password Hashes

If you need to reset a password:

```bash
cd src/dandiannotations/webapp
python3 -c "
import bcrypt
password = input('Enter new password: ')
hash_val = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print('Password hash:', hash_val)
"
```

Then update the hash in `moderators.yaml`.
