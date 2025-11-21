import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Add scan-attendance to path so we can import lambda_function
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'scan-attendance')))
import lambda_function as scan_lambda

def mock_event(valid=True):
    now = datetime.now(timezone.utc)
    qr_data = {
        "session_id": "sess-123",
        "class_id": "class-abc",
        "timestamp": now.isoformat(),
        "expiry": (now + timedelta(minutes=10)).isoformat()
    }
    if not valid:
        qr_data["expiry"] = (now - timedelta(minutes=1)).isoformat()

    return {
        "headers": {
            "Authorization": "Bearer dummy-token"
        },
        "body": json.dumps({
            "qr_code_data": json.dumps(qr_data)
        }),
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "student-001",
                    "cognito:groups": "students"
                }
            }
        }
    }

def test_valid_scan(monkeypatch):
    monkeypatch.setattr(scan_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "student-001"})
    monkeypatch.setattr(scan_lambda, "require_student", lambda u: True)
    monkeypatch.setattr(scan_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(scan_lambda, "validate_qr_code_data", lambda s: json.loads(s))
    monkeypatch.setattr(scan_lambda, "get_session", lambda sid: {"session_id": sid, "class_id": "class-abc", "is_active": True})
    monkeypatch.setattr(scan_lambda, "check_attendance_exists", lambda sid, uid: False)
    monkeypatch.setattr(scan_lambda, "create_attendance", lambda data: {"statusCode": 200})
    monkeypatch.setattr(scan_lambda, "get_class", lambda cid: {"class_name": "Intro to Testing"})
    monkeypatch.setattr(scan_lambda, "get_lecture_material_presigned_url", lambda **kwargs: None)
    monkeypatch.setattr(scan_lambda, "send_attendance_notification", lambda **kwargs: None)

    event = mock_event(valid=True)
    response = scan_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert "attendance recorded successfully" in response["body"]

def test_expired_qr(monkeypatch):
    monkeypatch.setattr(scan_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "student-001"})
    monkeypatch.setattr(scan_lambda, "require_student", lambda u: True)
    monkeypatch.setattr(scan_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(scan_lambda, "validate_qr_code_data", lambda s: None)  # simulate expired QR

    event = mock_event(valid=False)
    response = scan_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "invalid/expired QR code" in response["body"]