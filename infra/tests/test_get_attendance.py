import sys
import os
import json
import pytest

# Robust path handling
LAMBDA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'get-attendance'))
if LAMBDA_PATH not in sys.path:
    sys.path.append(LAMBDA_PATH)

import lambda_function as attendance_lambda


def mock_event(session_id="sess-123"):
    return {
        "httpMethod": "GET",
        "queryStringParameters": {"session_id": session_id},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "prof-001",
                    "cognito:groups": "professors"
                }
            }
        }
    }


def test_professor_get_attendance_success(monkeypatch):
    # Mock Identity Enrichment
    # This prevents the test from trying to connect to real Cognito
    monkeypatch.setattr(attendance_lambda, "get_email_from_sub", lambda sub: f"{sub}@example.com")

    # Mock Auth and Utils
    monkeypatch.setattr(attendance_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(attendance_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(attendance_lambda, "require_student", lambda u: False)
    monkeypatch.setattr(attendance_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(attendance_lambda, "get_session", lambda sid: {"session_id": sid, "class_id": "class-abc"})
    monkeypatch.setattr(attendance_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})
    monkeypatch.setattr(attendance_lambda, "get_attendance_by_session", lambda sid: [
        {"student_id": "stu-001"},
        {"student_id": "stu-002"}
    ])

    response = attendance_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["session_id"] == "sess-123"

    # Verify identity enrichment worked
    assert body["attendance_records"][0]["student_email"] == "stu-001@example.com"
    assert body["total_present"] == 2


def test_professor_get_attendance_unauthorized(monkeypatch):
    # Simulate a professor trying to access a session for a class they don't own
    monkeypatch.setattr(attendance_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(attendance_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(attendance_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(attendance_lambda, "get_session", lambda sid: {"session_id": sid, "class_id": "class-abc"})

    # Mock class owned by someone else
    monkeypatch.setattr(attendance_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "diff-prof-999"})

    response = attendance_lambda.lambda_handler(mock_event(), None)
    assert response["statusCode"] == 403