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

## Written Justification

We chose to use AWS Lambda instead of EC2 because our workload is entirely event-driven and triggered by user actions such as scanning QR codes or uploading materials. Lambda’s serverless architecture eliminates the need to manage any sort of infrastructure and is more suitable for bursty and unpredictable traffic patterns, which is to be expected from our project. 

AWS Simple Notification Service (SNS) handles real-time notifications specifically for attendance updates in our project. We chose this service over other solutions such as AWS Simple Queue Service (SQS) because SNS provides simple and scalable messaging with very minimal configuration. With SNS, we are able to broadcast notifications to subscribers instantly without manual polling or managing queues and can seamlessly integrate with our Lambda functions. 

We chose DynamoDB as our backend database rather than a service like AWS Relational Database Service (RDS) because all our data entries are key-value and non-relational, making DynamoDB’s flexible schema a better fit for our workload. Since queries for our project are predictable (by class_id, student_id, etc.), DynamoDB’s Global Secondary Indexes (GSI) provide us with efficient lookups that are useful for analytics and student tracking. 

We used Amazon S3 to store both QR codes and lecture materials. We chose Amazon S3 for storage over AWS Elastic Block Store (EBS) because S3 allows easy object-based storage access directly from the web, enabling students and professors to download materials or scan QR codes without a running server. Its seamless integration with CloudFront along with its scalability and easy access made it ideal for our project. 

We chose CloudFront for our front-end React application and for publicly served QR code images. Instead of accessing S3 directly, CloudFront ensures HTTPS delivery, fast response times, and ultimately better security. This improves user experience, especially for devices in classrooms or locations that have varying network speeds. 

We chose Cognito to manage user authentication and authorization for professors and students. This was chosen over other services such as custom JWT systems because Cognito integrates directly with API Gateway and simplifies secure sign-up, sign-in, and group-based access control. With Cognito, we avoided the complexity of building and maintaining our own authentication backend, handling password security, token refresh, and user group management manually. 

API Gateway exposes a unified REST interface for all backend functions of our project. We chose this over manually managing API endpoints on EC2 because it supports CORS, request validation, and integration with Lambda and Cognito. This ultimately made it easy to manage APIs across services in a secure and consistent manner. 