import sys
import os
import json

# Add get-analytics to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'get-analytics')))
import lambda_function as analytics_lambda

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

def test_get_session_analytics(monkeypatch):
    monkeypatch.setattr(analytics_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(analytics_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(analytics_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(analytics_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc",
        "session_date": "2025-11-20"
    })
    monkeypatch.setattr(analytics_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})
    monkeypatch.setattr(analytics_lambda, "get_attendance_by_session", lambda sid: [
        {"student_id": "stu-001", "scan_timestamp": "2025-11-20T10:00:00Z"},
        {"student_id": "stu-002", "scan_timestamp": "2025-11-20T10:01:00Z"}
    ])

    event = mock_event()
    response = analytics_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["session_id"] == "sess-123"
    assert body["class_id"] == "class-abc"
    assert body["analytics"]["attendance_rate"] == 100.0
    assert body["analytics"]["present_count"] == 2
    assert body["analytics"]["absent_count"] == 0
    assert len(body["analytics"]["scan_times"]) == 2