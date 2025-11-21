import sys
import os
import json
from datetime import datetime, timezone

# Add manage-sessions to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'manage-sessions')))
import lambda_function as manage_lambda

def mock_event():
    return {
        "httpMethod": "POST",
        "headers": {"Authorization": "Bearer dummy"},
        "body": json.dumps({
            "class_id": "class-abc",
            "session_date": "2025-11-21",
            "start_time": "10:00",
            "end_time": "11:00"
        }),
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "prof-001",
                    "cognito:groups": "professors"
                }
            }
        }
    }

def test_create_session_success(monkeypatch):
    monkeypatch.setattr(manage_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(manage_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(manage_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(manage_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})
    monkeypatch.setattr(manage_lambda.qr_generator, "generate_and_upload_qr_code",
                        lambda sid, cid: {"qr_code_url": "https://example.com/qr.png"})
    monkeypatch.setattr(manage_lambda, "create_session",
                        lambda data: {"statusCode": 200, "session_id": data["session_id"]})
    
    event = mock_event()
    response = manage_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["class_id"] == "class-abc"
    assert body["qr_code_url"] == "https://example.com/qr.png"
    assert body["is_active"] is True