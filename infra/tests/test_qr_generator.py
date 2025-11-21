import pytest
from datetime import datetime, timedelta
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lambdas', 'shared')))
from qr_generator import validate_qr_code_data

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
    assert result["session_id"] == "sess-123"
    assert result["class_id"] == "class-abc"

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
    assert result is None