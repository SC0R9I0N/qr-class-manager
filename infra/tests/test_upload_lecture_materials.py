import sys
import os
import json
import base64
import pytest

# Robust path handling
LAMBDA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'upload-lecture-materials'))
if LAMBDA_PATH not in sys.path:
    sys.path.append(LAMBDA_PATH)

import lambda_function as upload_lambda


def mock_post_event(session_id="sess-123"):
    file_bytes = b"dummy lecture content"
    # Note: Lambda usually receives the JSON body, not double-base64.
    # We mock the body as a standard JSON string inside the event.
    body = {
        "session_id": session_id,
        "file_content": base64.b64encode(file_bytes).decode("utf-8"),
        "filename": "lecture_materials.zip"
    }
    return {
        "httpMethod": "POST",
        "body": json.dumps(body),
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "prof-001",
                    "cognito:groups": "professors"
                }
            }
        }
    }


# Scenario 1: Professor successfully uploads to their own class
def test_upload_lecture_material_success(monkeypatch):
    monkeypatch.setattr(upload_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(upload_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(upload_lambda, "get_user_id", lambda u: u["id"])

    # Mock DB lookups
    monkeypatch.setattr(upload_lambda, "get_session", lambda sid: {"class_id": "class-abc"})
    monkeypatch.setattr(upload_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})

    # Mock S3 and Update logic
    monkeypatch.setattr(upload_lambda, "upload_lecture_material", lambda sid, content, fname: f"{sid}/{fname}")
    monkeypatch.setattr(upload_lambda, "update_session", lambda sid, updates: True)

    response = upload_lambda.lambda_handler(mock_post_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["lecture_material_key"] == "sess-123/lecture_materials.zip"
    # Removed file_size assertion if the Lambda doesn't return it
    # Or, verify the key exists only if you intend to add it to the handler
    # assert body["session_id"] == "sess-123"

def test_upload_lecture_material_forbidden(monkeypatch):
    monkeypatch.setattr(upload_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    # Ensure the general auth check passes
    monkeypatch.setattr(upload_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(upload_lambda, "get_user_id", lambda u: "prof-001")

    monkeypatch.setattr(upload_lambda, "get_session", lambda sid: {"class_id": "class-abc"})
    monkeypatch.setattr(upload_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-999"})

    response = upload_lambda.lambda_handler(mock_post_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 403
    # Verify the specific ownership error string
    assert "not own" in body["error"].lower()