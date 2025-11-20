# Backend Lambda Functions

This directory contains all backend Lambda functions for the QR Code Class Attendance

## Project Structure

```
lambdas/
├── shared/                    # Shared utilities and helpers
│   ├── __init__.py
│   ├── models.py             # Data models and schemas
│   ├── dynamodb_utils.py     # DynamoDB operations
│   ├── qr_generator.py       # QR code generation and validation
│   ├── auth_utils.py         # Cognito authentication helpers
│   ├── s3_utils.py           # S3 operations
│   └── sns_utils.py          # SNS notification utilities
│
├── generate-qr/              # Generate QR codes for class sessions
│   ├── __init__.py
│   ├── lambda_function.py
│   └── requirements.txt
│
├── scan-attendance/          # Handle student QR code scans
│   ├── __init__.py
│   ├── lambda_function.py
│   └── requirements.txt
│
├── get-attendance/           # Retrieve attendance records
│   ├── __init__.py
│   ├── lambda_function.py
│   └── requirements.txt
│
├── get-analytics/            # Get attendance analytics and statistics
│   ├── __init__.py
│   ├── lambda_function.py
│   └── requirements.txt
│
├── manage-sessions/          # Create/manage class sessions (CRUD)
│   ├── __init__.py
│   ├── lambda_function.py
│   └── requirements.txt
│
├── upload-lecture-materials/ # Upload lecture materials (zip files) for sessions
│   ├── __init__.py
│   ├── lambda_function.py
│   └── requirements.txt
│
└── get-lecture-materials/    # Get/download lecture materials for students
    ├── __init__.py
    ├── lambda_function.py
    └── requirements.txt
```

## Lambda Functions

### 1. generate-qr
Generates unique QR codes for class sessions

**Endpoint:** `POST /sessions/{session_id}/qr-code`

**Request Body:**
```json
{
  "session_id": "string",
  "expiry_minutes": 60  // optional, default: 60
}
```

**Response:**
```json
{
  "session_id": "string",
  "qr_code_url": "https://...",
  "qr_code_data": {
    "session_id": "string",
    "class_id": "string",
    "timestamp": "ISO8601",
    "expiry": "ISO8601"
  },
  "expires_at": "ISO8601"
}
```

**Authorization:** Professors only

---

### 2. scan-attendance
Processes student QR code scans to mark attendance

**Endpoint:** `POST /attendance/scan`

**Request Body:**
```json
{
  "qr_code_data": "JSON string from scanned QR code",
  "location": "string (optional)",
  "device_info": "string (optional)"
}
```

**Response:**
```json
{
  "attendance_id": "string",
  "session_id": "string",
  "class_id": "string",
  "class_name": "string",
  "scan_timestamp": "ISO8601",
  "message": "Attendance recorded successfully"
}
```

**Authorization:** Students only

**Notes:**
- Prevents duplicate attendance for the same session
- Validates QR code expiry
- Sends SNS notification on success with lecture material info (if available)

---

### 3. get-attendance
Retrieves attendance records with filtering options

**Endpoint:** `GET /attendance`

**Query Parameters:**
- `session_id` (optional): Get attendance for a specific session (professors only)
- `class_id` (optional): Get attendance for a class
- `student_id` (optional): Get attendance for a specific student (professors only)

**Response:**
```json
{
  "session_id": "string",  // if querying by session
  "class_id": "string",    // if querying by class
  "student_id": "string",  // if querying by student
  "attendance_count": 10,
  "attendance": [...]
}
```

**Authorization:** 
- Professors: Can view any attendance
- Students: Can only view their own attendance

---

### 4. get-analytics
Retrieves attendance analytics and statistics

**Endpoint:** `GET /analytics`

**Query Parameters:**
- `class_id` (required for class analytics): Get analytics for a class
- `session_id` (optional): Get analytics for a specific session

**Response (Session Analytics):**
```json
{
  "session_id": "string",
  "class_id": "string",
  "session_date": "YYYY-MM-DD",
  "analytics": {
    "total_students": 30,
    "present_count": 25,
    "absent_count": 5,
    "attendance_rate": 83.33,
    "scan_times": [...]
  }
}
```

**Response (Class Analytics):**
```json
{
  "class_id": "string",
  "class_name": "string",
  "analytics": {
    "total_sessions": 10,
    "total_students": 30,
    "average_attendance_per_session": 25.5,
    "session_analytics": [...],
    "student_attendance_rates": {
      "student_id": 85.5,
      ...
    }
  }
}
```

**Authorization:** Professors only

---

### 5. manage-sessions
CRUD operations for class sessions

**Endpoints:**
- `GET /sessions?class_id={class_id}` - List all sessions for a class
- `GET /sessions?session_id={session_id}` - Get a specific session
- `POST /sessions` - Create a new session
- `PUT /sessions` - Update a session
- `DELETE /sessions?session_id={session_id}` - Deactivate a session

**Create Session Request:**
```json
{
  "class_id": "string",
  "session_date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM"  // optional
}
```

**Update Session Request:**
```json
{
  "session_id": "string",
  "session_date": "YYYY-MM-DD",  // optional
  "start_time": "HH:MM",          // optional
  "end_time": "HH:MM",            // optional
  "is_active": true               // optional
}
```

**Authorization:** Professors only

---

## Environment Variables

The following environment variables should be configured for each Lambda function:

### Required
- `CLASSES_TABLE` - DynamoDB table name for classes (default: `classes`)
- `SESSIONS_TABLE` - DynamoDB table name for sessions (default: `sessions`)
- `ATTENDANCE_TABLE` - DynamoDB table name for attendance (default: `attendance`)
- `QR_CODE_BUCKET` - S3 bucket name for storing QR code images
- `LECTURE_MATERIALS_BUCKET` - S3 bucket name for storing lecture materials (default: `qr-class-manager-lectures`)
- `USER_POOL_ID` - Cognito User Pool ID
- `COGNITO_CLIENT_ID` - Cognito App Client ID

### Optional
- `CLOUDFRONT_DOMAIN` - CloudFront domain for QR code URLs (if using CloudFront)
- `ATTENDANCE_TOPIC_ARN` - SNS topic ARN for attendance notifications
- `AWS_REGION` - AWS region (default: `us-east-1`)

## DynamoDB Table Structure

### Classes Table
- **Partition Key:** `class_id` (String)
- **GSI:** `professor_id-index` (Partition Key: `professor_id`)

### Sessions Table
- **Partition Key:** `session_id` (String)
- **GSI:** `class_id-index` (Partition Key: `class_id`)
- **Fields:** `lecture_material_url`, `lecture_material_key` (optional, for lecture materials)

### Attendance Table
- **Partition Key:** `attendance_id` (String)
- **GSI:** `session_id-index` (Partition Key: `session_id`)
- **GSI:** `student_id-index` (Partition Key: `student_id`)
- **GSI:** `student_class-index` (Partition Key: `student_id`, Sort Key: `class_id`)
- **GSI:** `session_student-index` (Partition Key: `session_id`, Sort Key: `student_id`)

## Dependencies

All Lambda functions require:
- `boto3>=1.28.0` - AWS SDK
- `python-jose[cryptography]>=3.3.0` - JWT token handling

Functions that generate QR codes also require:
- `qrcode[pil]>=7.4.2` - QR code generation

## Shared Utils

### dynamodb_utils.py
Helper functions for DynamoDB operations:
- `create_class()`, `get_class()`, `get_classes_by_professor()`
- `create_session()`, `get_session()`, `get_sessions_by_class()`, `update_session()`
- `create_attendance()`, `get_attendance_by_session()`, `get_attendance_by_student()`, `check_attendance_exists()`

### qr_generator.py
QR code generation and validation:
- `generate_qr_code_data()` - Create QR code data structure
- `create_qr_code_image()` - Generate QR code PNG image
- `upload_qr_code_to_s3()` - Upload QR code to S3
- `generate_and_upload_qr_code()` - Complete QR code generation workflow
- `validate_qr_code_data()` - Validate scanned QR code data

### auth_utils.py
Cognito authentication helpers:
- `get_user_from_event()` - Extract user info from API Gateway event
- `verify_token()` - Verify JWT tokens
- `require_professor()`, `require_student()` - Role checks
- `get_user_id()` - Extract user ID

### s3_utils.py
S3 operations:
- `get_presigned_url()` - Generate presigned URLs
- `delete_object()` - Delete S3 objects
- `upload_lecture_material()` - Upload lecture materials (zip files) to S3
- `get_lecture_material_presigned_url()` - Get presigned URL for downloading lecture materials
- `delete_lecture_material()` - Delete lecture materials from S3

### sns_utils.py
SNS notifications:
- `send_attendance_notification()` - Send attendance confirmation notifications (includes lecture material info if available)
- `send_bulk_notification()` - Send custom notifications

### models.py
Data models:
- `Class` - Class/course model
- `Session` - Class session model
- `Attendance` - Attendance record model
- `QRCodeData` - QR code data structure

## API Gateway Integration

All Lambda functions are designed to work with API Gateway REST API events. They expect:
- Cognito User Pool authorizer for authentication
- Request body in `event['body']` (may be JSON string or dict)
- Query parameters in `event['queryStringParameters']`
- HTTP method in `event['httpMethod']` or `event['requestContext']['http']['method']`

## Notes

1. **QR Code Expiry:** QR codes expire after a configurable time (default: 60 minutes). Expired QR codes cannot be used to mark attendance.

2. **Duplicate Prevention:** The system prevents students from marking attendance multiple times for the same session.

3. **Authorization:** All endpoints require authentication via Cognito. Role-based access control ensures:
   - Professors can manage sessions, generate QR codes, and view all attendance
   - Students can only scan QR codes and view their own attendance

4. **SNS Notifications:** Attendance confirmations are sent via SNS when students successfully mark attendance. The notification includes lecture material download information if materials are available for the session.

5. **Lecture Materials:** Professors can upload zip files containing lecture materials for each session. When students scan QR codes for attendance, the SNS notification includes a presigned URL (valid for 24 hours) to download the materials. Students must have marked attendance before they can download materials.

5. **Shared Code:** The `shared/` directory contains reusable utilities. When deploying, make sure the shared code is accessible to all Lambda functions (use Lambda Layers).