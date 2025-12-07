import sys
import os
import json
import pytest

# Robust path handling
LAMBDA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'manage-sessions'))
if LAMBDA_PATH not in sys.path:
    sys.path.append(LAMBDA_PATH)

import lambda_function as manage_lambda


def mock_post_event(class_id="class-abc"):
    return {
        "httpMethod": "POST",
        "body": json.dumps({
            "class_id": class_id,
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


# Scenario 1: Professor successfully creates a session
def test_create_session_success(monkeypatch):
    # 1. Mock the specific functions imported 'from dynamodb_utils'
    # We mock them directly on the 'manage_lambda' module
    monkeypatch.setattr(manage_lambda, "get_class",
                        lambda cid: {"class_id": cid, "professor_id": "prof-001"})

    # Mock the exact name used in your Lambda handler
    monkeypatch.setattr(manage_lambda, "create_session",
                        lambda data: {"statusCode": 200})  # Returns success code

    # 2. Mock auth utilities
    monkeypatch.setattr(manage_lambda, "get_user_from_event",
                        lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(manage_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(manage_lambda, "get_user_id", lambda u: "prof-001")

    # 3. Mock QR Generator imported 'from shared import qr_generator'
    # Note: Access via manage_lambda.qr_generator because of how it's imported
    monkeypatch.setattr(manage_lambda.qr_generator, "generate_and_upload_qr_code",
                        lambda sid, cid: {"qr_code_url": "https://example.com/qr.png"})

    # Execute
    response = manage_lambda.lambda_handler(mock_post_event(), None)

    # Assert
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["qr_code_url"] == "https://example.com/qr.png"


def test_create_session_forbidden(monkeypatch):
    monkeypatch.setattr(manage_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(manage_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(manage_lambda, "get_user_id", lambda u: "prof-001")

    monkeypatch.setattr(manage_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-999"})

    response = manage_lambda.lambda_handler(mock_post_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 403
    assert "not own" in body["error"].lower()


def test_create_session_bad_request(monkeypatch):
    monkeypatch.setattr(manage_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(manage_lambda, "require_professor", lambda u: True)

    event = mock_post_event()
    event["body"] = json.dumps({"session_date": "2025-11-21"})

    response = manage_lambda.lambda_handler(event, None)

    # If it returns 403, your handler is checking if body is empty or malformed
    # and treating it as an auth failure, adjust expectation or handler
    assert response["statusCode"] == 400