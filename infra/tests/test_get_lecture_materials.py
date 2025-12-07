import sys
import os
import json
import pytest

# Robust path handling
LAMBDA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'get-lecture-materials'))
if LAMBDA_PATH not in sys.path:
    sys.path.append(LAMBDA_PATH)

import lambda_function as lecture_lambda

def mock_event(session_id="sess-123"):
    return {
        "httpMethod": "GET",
        "queryStringParameters": {"session_id": session_id},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "stu-001",
                    "cognito:groups": "students"
                }
            }
        }
    }

# Scenario 1: Student successfully downloads material they attended
def test_get_lecture_material_success(monkeypatch):
    monkeypatch.setattr(lecture_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "stu-001"})
    monkeypatch.setattr(lecture_lambda, "require_student", lambda u: True)
    monkeypatch.setattr(lecture_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(lecture_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc",
        "lecture_material_key": "sess-123/lecture_materials.zip"
    })
    # Mocking that the student DID attend
    monkeypatch.setattr(lecture_lambda, "check_attendance_exists", lambda sid, uid: True)
    monkeypatch.setattr(lecture_lambda, "get_lecture_material_presigned_url", lambda **kwargs: "https://example.com/url")
    monkeypatch.setattr(lecture_lambda, "get_class", lambda cid: {"class_id": cid, "class_name": "Intro to Testing"})

    response = lecture_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["download_url"] == "https://example.com/url"
    assert body["class_name"] == "Intro to Testing"

# Scenario 2: Student blocked because they didn't attend
def test_get_lecture_material_forbidden(monkeypatch):
    monkeypatch.setattr(lecture_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "stu-001"})
    monkeypatch.setattr(lecture_lambda, "require_student", lambda u: True)
    monkeypatch.setattr(lecture_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(lecture_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc"
    })
    monkeypatch.setattr(lecture_lambda, "check_attendance_exists", lambda sid, uid: False)

    response = lecture_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 403
    assert "mark attendance" in body["error"].lower()


def test_get_lecture_material_missing_file(monkeypatch):
    monkeypatch.setattr(lecture_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "stu-001"})
    monkeypatch.setattr(lecture_lambda, "require_student", lambda u: True)
    monkeypatch.setattr(lecture_lambda, "get_user_id", lambda u: u["id"])

    monkeypatch.setattr(lecture_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc",
        "lecture_material_key": None  # No file uploaded
    })

    monkeypatch.setattr(lecture_lambda, "get_class", lambda cid: {"class_id": cid, "class_name": "Testing"})

    # Mock successful attendance
    monkeypatch.setattr(lecture_lambda, "check_attendance_exists", lambda sid, uid: True)

    response = lecture_lambda.lambda_handler(mock_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 404
    assert "no lecture material" in body["error"].lower()