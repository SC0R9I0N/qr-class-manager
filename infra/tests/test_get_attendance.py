import sys
import os
import json

# Add get-attendance to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'get-attendance')))
import lambda_function as attendance_lambda

def mock_event():
    return {
        "httpMethod": "GET",
        "headers": {"Authorization": "Bearer dummy"},
        "queryStringParameters": {
            "session_id": "sess-123"
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "prof-001",
                    "cognito:groups": "professors"
                }
            }
        }
    }

def test_professor_get_attendance_by_session(monkeypatch):
    monkeypatch.setattr(attendance_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(attendance_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(attendance_lambda, "require_student", lambda u: False)
    monkeypatch.setattr(attendance_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(attendance_lambda, "get_session", lambda sid: {"session_id": sid, "class_id": "class-abc"})
    monkeypatch.setattr(attendance_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})
    monkeypatch.setattr(attendance_lambda, "get_attendance_by_session", lambda sid: [
        {"student_id": "stu-001", "status": "present"},
        {"student_id": "stu-002", "status": "present"}
    ])

    event = mock_event()
    response = attendance_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["session_id"] == "sess-123"
    assert body["class_id"] == "class-abc"
    assert body["attendance_count"] == 2
    assert len(body["attendance"]) == 2