import pytest
from datetime import datetime, timedelta
import json
import sys
import os

# Ensuring path to shared utilities
SHARED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'shared'))
if SHARED_PATH not in sys.path:
    sys.path.append(SHARED_PATH)

from qr_generator import validate_qr_code_data

# Valid Flow
def test_valid_qr_code():
    now = datetime.utcnow()
    qr_data = {
        "session_id": "sess-123",
        "class_id": "class-abc",
        "timestamp": now.isoformat(),
        "expiry": (now + timedelta(minutes=10)).isoformat()
    }
    qr_string = json.dumps(qr_data)
    result = validate_qr_code_data(qr_string)
    assert result is not None
    assert result["session_id"] == "sess-123"

# Expired Flow: Verify the 1-hour old code is rejected
def test_expired_qr_code():
    now = datetime.utcnow()
    qr_data = {
        "session_id": "sess-123",
        "class_id": "class-abc",
        "timestamp": (now - timedelta(hours=2)).isoformat(),
        "expiry": (now - timedelta(hours=1)).isoformat()
    }
    qr_string = json.dumps(qr_data)
    result = validate_qr_code_data(qr_string)
    assert result is None  # Logic should return None if current time > expiry

# Integrity Flow: JSON is missing critical keys
def test_incomplete_qr_data():
    qr_data = {"session_id": "sess-123"} # Missing class_id and expiry
    qr_string = json.dumps(qr_data)
    result = validate_qr_code_data(qr_string)
    assert result is None

# Corruption Flow: String is not valid JSON
def test_invalid_json_format():
    qr_string = "not-a-json-string-but-a-spoof-attempt"
    result = validate_qr_code_data(qr_string)
    assert result is None