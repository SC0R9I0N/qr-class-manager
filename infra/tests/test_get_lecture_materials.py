import sys
import os
import json

# Add get-lecture-materials to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'get-lecture-materials')))
import lambda_function as lecture_lambda

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
                    "cognito:username": "stu-001",
                    "cognito:groups": "students"
                }
            }
        }
    }

def test_get_lecture_material_success(monkeypatch):
    monkeypatch.setattr(lecture_lambda, "get_user_from_event", lambda e: {"role": "student", "id": "stu-001"})
    monkeypatch.setattr(lecture_lambda, "require_student", lambda u: True)
    monkeypatch.setattr(lecture_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(lecture_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc",
        "session_date": "2025-11-20",
        "lecture_material_key": "sess-123/lecture_materials.zip"
    })
    monkeypatch.setattr(lecture_lambda, "check_attendance_exists", lambda sid, uid: True)
    monkeypatch.setattr(lecture_lambda, "get_lecture_material_presigned_url", lambda **kwargs: "https://example.com/presigned-url")
    monkeypatch.setattr(lecture_lambda, "get_class", lambda cid: {"class_id": cid, "class_name": "Intro to Testing"})

    event = mock_event()
    response = lecture_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["session_id"] == "sess-123"
    assert body["class_id"] == "class-abc"
    assert body["class_name"] == "Intro to Testing"
    assert body["download_url"] == "https://example.com/presigned-url"
    assert body["expires_in"] == 3600