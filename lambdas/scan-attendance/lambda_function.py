import json
import os
import sys
import uuid
from datetime import datetime

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from qr_generator import validate_qr_code_data
from dynamodb_utils import (
    get_session, create_attendance, check_attendance_exists,
    get_class
)
from auth_utils import get_user_from_event, require_student, get_user_id
from sns_utils import send_attendance_notification


def lambda_handler(event, context):
    """
    Expected event body:
    {
        "qr_code_data": "string (JSON string from scanned QR code)",
        "location": "string (optional)",
        "device_info": "string (optional)"
    }
    """
    try:
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # user is a student
        if not require_student(user):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'only students can scan attendance'})
            }
        
        student_id = get_user_id(user)
        if not student_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'cannot identify student'})
            }
        
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        qr_code_string = body.get('qr_code_data')
        if not qr_code_string:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'qr_code_data is required'})
            }
        
        qr_data = validate_qr_code_data(qr_code_string)
        if not qr_data:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'invalid/expired QR code'})
            }
        
        session_id = qr_data['session_id']
        class_id = qr_data['class_id']
        
        # make sure session exists and is active
        session = get_session(session_id)
        if not session:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'session not found'})
            }
        
        if not session.get('is_active', False):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'session not active'})
            }
        
        # make sure session belongs to the class in QR code
        if session.get('class_id') != class_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'QR code does not match session'})
            }
        
        # check if student has already marked attendance
        if check_attendance_exists(session_id, student_id):
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Attendance already recorded',
                    'message': 'you have already marked attendance for this session'
                })
            }
        
        # attendance record
        attendance_id = str(uuid.uuid4())
        scan_timestamp = datetime.utcnow().isoformat()
        
        attendance_data = {
            'attendance_id': attendance_id,
            'session_id': session_id,
            'class_id': class_id,
            'student_id': student_id,
            'scan_timestamp': scan_timestamp,
            'location': body.get('location'),
            'device_info': body.get('device_info')
        }
        
        result = create_attendance(attendance_data)
        
        if result.get('statusCode') != 200:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'failed to record attendance'})
            }
        
        # send noti
        send_attendance_notification(
            student_id=student_id,
            session_id=session_id,
            class_id=class_id,
            message_type='attendance_confirmed'
        )
        
        class_data = get_class(class_id)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'attendance_id': attendance_id,
                'session_id': session_id,
                'class_id': class_id,
                'class_name': class_data.get('class_name') if class_data else None,
                'scan_timestamp': scan_timestamp,
                'message': 'attendance recorded successfully'
            })
        }
    
    except Exception as e:
        print(f"Error scanning attendance: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

