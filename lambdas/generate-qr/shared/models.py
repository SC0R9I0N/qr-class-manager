from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Class:
    class_id: str
    professor_id: str
    class_name: str
    class_code: str
    created_at: str
    updated_at: Optional[str] = None

@dataclass
class Session:
    session_id: str
    class_id: str
    session_date: str
    start_time: str
    end_time: Optional[str] = None
    qr_code_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    is_active: bool = True
    created_at: str = None

@dataclass
class Attendance:
    attendance_id: str
    session_id: str
    class_id: str
    student_id: str
    scan_timestamp: str
    location: Optional[str] = None
    device_info: Optional[str] = None

@dataclass
class QRCodeData:
    session_id: str
    class_id: str
    timestamp: str
    expiry: Optional[str] = None

