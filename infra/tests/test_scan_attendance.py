import sys
import os
import json
import pytest
from datetime import datetime, timedelta, timezone

# Robust path handling
LAMBDA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'scan-attendance'))
if LAMBDA_PATH not in sys.path:
    sys.path.append(LAMBDA_PATH)

import lambda_function as scan_lambda


def mock_event(valid=True):
    now = datetime.now(timezone.utc)
    qr_data = {
        "session_id": "sess-123",
        "class_id": "class-abc",
        "expiry": (now + (timedelta(minutes=10) if valid else timedelta(minutes=-1))).isoformat()
    }
    return {
        "body": json.dumps({"qr_code_data": json.dumps(qr_data)}),
        "requestContext": {"authorizer": {"claims": {"cognito:username": "stu-01"}}}
    }


# Scenario 1: Successful first-time scan
def test_valid_scan_success(monkeypatch):
    monkeypatch.setattr(scan_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "student-001"})
    monkeypatch.setattr(scan_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(scan_lambda, "validate_qr_code_data", lambda s: json.loads(s))

    # 🟢 Mock the exact names imported into the lambda namespace
    monkeypatch.setattr(scan_lambda, "get_session", lambda sid: {"is_active": True, "class_id": "class-abc"})
    monkeypatch.setattr(scan_lambda, "get_class", lambda cid: {"class_name": "Test Class"})
    monkeypatch.setattr(scan_lambda, "check_attendance_exists", lambda sid, uid: False)
    monkeypatch.setattr(scan_lambda, "create_attendance", lambda d: {"statusCode": 200})

    # Pre-signed URL mock
    monkeypatch.setattr(scan_lambda, "get_lecture_material_presigned_url", lambda **k: "https://dl.com/file")

    response = scan_lambda.lambda_handler(mock_event(), None)
    assert response["statusCode"] == 200


def test_scan_duplicate_attendance(monkeypatch):
    monkeypatch.setattr(scan_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "student-001"})
    monkeypatch.setattr(scan_lambda, "validate_qr_code_data", lambda s: json.loads(s))
    monkeypatch.setattr(scan_lambda, "get_session", lambda sid: {"is_active": True, "class_id": "class-abc"})
    monkeypatch.setattr(scan_lambda, "check_attendance_exists", lambda sid, uid: True)

    response = scan_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    # 🟢 FIXED: Match actual string 'already marked'
    assert "already marked" in body["message"].lower()


def test_scan_inactive_session(monkeypatch):
    monkeypatch.setattr(scan_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "student-001"})
    monkeypatch.setattr(scan_lambda, "validate_qr_code_data", lambda s: json.loads(s))
    monkeypatch.setattr(scan_lambda, "get_session", lambda sid: {"is_active": False})

    response = scan_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    # 🟢 FIXED: Match actual string 'inactive'
    assert "inactive" in body["error"].lower()