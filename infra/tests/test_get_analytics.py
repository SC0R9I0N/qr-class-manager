import sys
import os
import json
import pytest

# Robust path handling to reach the Lambda handler
LAMBDA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'get-analytics'))
if LAMBDA_PATH not in sys.path:
    sys.path.append(LAMBDA_PATH)

import lambda_function as analytics_lambda


def mock_event(session_id="sess-123", username="prof-001"):
    return {
        "httpMethod": "GET",
        "queryStringParameters": {"session_id": session_id},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": username,
                    "cognito:groups": "professors"
                }
            }
        }
    }


def test_get_session_analytics_success(monkeypatch):
    # Mocking standard auth and DB functions
    monkeypatch.setattr(analytics_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(analytics_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(analytics_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(analytics_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc"
    })
    monkeypatch.setattr(analytics_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})
    monkeypatch.setattr(analytics_lambda, "get_attendance_by_session", lambda sid: [
        {"student_id": "stu-01", "scan_timestamp": "2025-11-20T10:00:00Z"},
        {"student_id": "stu-02", "scan_timestamp": "2025-11-20T10:01:00Z"}
    ])

    response = analytics_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["analytics"]["present_count"] == 2
    assert body["class_id"] == "class-abc"


# Security Path: Professor attempts to get analytics for a class they DON'T own
def test_get_session_analytics_forbidden(monkeypatch):
    monkeypatch.setattr(analytics_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(analytics_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(analytics_lambda, "get_user_id", lambda u: u["id"])

    monkeypatch.setattr(analytics_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-other"  # Different class
    })
    # Professor ID in DB does not match prof-001
    monkeypatch.setattr(analytics_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-999"})

    response = analytics_lambda.lambda_handler(mock_event(), None)
    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert "own this class" in body["error"]