# ClassBits

---

# Frontend Integration Guide

This document provides everything the frontend team needs to integrate with the backend and AWS infrastructure for ClassBits.

---

## Authentication (Cognito)

| **Item** | **Value** |
|----------|-----------|
| Cognito User Pool ID | `us-east-1_z61jO4Mni` |
| Cognito App Client ID | `6pfufvg52tejjmoa03rigpev8i` |
| Cognito Region | `us-east-1` |
| Token Usage | `Authorization: Bearer <access_token>` |

### Test Users

| **Role** | **Email** | **Password** |
|----------|-----------|--------------|
| Professor | `prof@example.com` | `SecurePass123!` |
| Student   | `student1@example.com` | `StrongPass123!` |

---

## Sample Cognito Auth Commands

### 1. Get ID Token (Initial Login)

```bash
aws cognito-idp initiate-auth \
  --region us-east-1 \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6pfufvg52tejjmoa03rigpev8i \
  --auth-parameters USERNAME=student1@example.com,PASSWORD=StrongPass123!
```

Returns:

```json
{
  "AuthenticationResult": {
    "IdToken": "...",
    "AccessToken": "...",
    "RefreshToken": "...",
    ...
  }
}
```

---

### 2. Refresh ID Token Using Refresh Token

```bash
aws cognito-idp initiate-auth \
  --region us-east-1 \
  --auth-flow REFRESH_TOKEN_AUTH \
  --client-id 6pfufvg52tejjmoa03rigpev8i \
  --auth-parameters REFRESH_TOKEN=<your_refresh_token>
```

---

### 3. First-Time Login Password Challenge (if applicable)

If a student account was created with a temporary password and triggers a `NEW_PASSWORD_REQUIRED` challenge:

```bash
aws cognito-idp respond-to-auth-challenge \
  --region us-east-1 \
  --client-id 6pfufvg52tejjmoa03rigpev8i \
  --challenge-name NEW_PASSWORD_REQUIRED \
  --challenge-responses USERNAME=student1@example.com,NEW_PASSWORD=StrongPass123!,PASSWORD=StrongPass123! \
  --session <session_token_from_previous_response>
```

---

## API Gateway

| **Item** | **Value** |
|----------|-----------|
| Base URL | `https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/` |

---

## API Endpoints

| **Endpoint** | **Method(s)** | **Description** |
|--------------|---------------|-----------------|
| `/sessions` | `GET`, `POST`, `PUT`, `DELETE` | Manage class sessions |
| `/sessions/{session_id}/qr-code` | `POST` | Generate QR code for attendance |
| `/attendance` | `GET` | View attendance (student or professor) |
| `/attendance/scan` | `POST` | Submit attendance via QR scan |
| `/analytics` | `GET` | View attendance analytics |
| `/materials` | `GET`, `POST` | Upload/download lecture materials |

---

## File Upload Format

- Endpoint: `POST /materials`
- Format: `multipart/form-data`
- File type: `.zip`
- Expected structure inside zip:
  ```
  slides/
  notes/
  readings/
  ```

---

## Role-Based Access

| **Role** | **Access** |
|----------|------------|
| `student` | View attendance, scan QR, download materials |
| `professor` | Manage sessions, generate QR, upload materials, view analytics |

---

## CORS Configuration

CORS is enabled for all frontend-accessible endpoints.

### Preflight Test

```bash
curl -i -X OPTIONS https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/attendance \
  -H "Origin: https://example-frontend.com" \
  -H "Access-Control-Request-Method: GET"
```

Expected headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: OPTIONS,GET,POST,PUT,DELETE
Access-Control-Allow-Headers: Authorization,Content-Type
```

---

### Authenticated Request Test

```bash
curl -i -X GET https://7ql71igsye.execute-api.us-east-1.amazonaws.com/prod/attendance \
  -H "Origin: https://example-frontend.com" \
  -H "Authorization: Bearer <valid_id_token>"
```

Expected: `200 OK` with JSON response and CORS headers.
