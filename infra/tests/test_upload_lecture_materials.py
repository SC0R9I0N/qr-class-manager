import sys
import os
import json
import base64

# Add upload-lecture-materials to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'upload-lecture-materials')))
import lambda_function as upload_lambda

def mock_event():
    file_bytes = b"dummy lecture content"
    encoded = base64.b64encode(json.dumps({
        "session_id": "sess-123",
        "file_content": base64.b64encode(file_bytes).decode("utf-8"),
        "filename": "lecture_materials.zip"
    }).encode("utf-8")).decode("utf-8")

    return {
        "httpMethod": "POST",
        "isBase64Encoded": True,
        "body": encoded,
        "headers": {"Authorization": "Bearer dummy"},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "cognito:username": "prof-001",
                    "cognito:groups": "professors"
                }
            }
        }
    }

def test_upload_lecture_material_success(monkeypatch):
    monkeypatch.setattr(upload_lambda, "get_user_from_event", lambda e: {"role": "professor", "id": "prof-001"})
    monkeypatch.setattr(upload_lambda, "require_professor", lambda u: True)
    monkeypatch.setattr(upload_lambda, "get_user_id", lambda u: u["id"])
    monkeypatch.setattr(upload_lambda, "get_session", lambda sid: {
        "session_id": sid,
        "class_id": "class-abc",
        "lecture_material_key": None
    })
    monkeypatch.setattr(upload_lambda, "get_class", lambda cid: {"class_id": cid, "professor_id": "prof-001"})
    monkeypatch.setattr(upload_lambda, "upload_lecture_material", lambda sid, content, fname: f"{sid}/{fname}")
    monkeypatch.setattr(upload_lambda, "update_session", lambda sid, updates: True)
    monkeypatch.setattr(upload_lambda, "delete_lecture_material", lambda key: None)

    event = mock_event()
    response = upload_lambda.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["session_id"] == "sess-123"
    assert body["lecture_material_key"] == "sess-123/lecture_materials.zip"
    assert body["filename"] == "lecture_materials.zip"
    assert body["file_size"] == len(b"dummy lecture content")