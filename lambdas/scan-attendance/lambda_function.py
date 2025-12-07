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
from s3_utils import get_lecture_material_presigned_url

# Define Universal CORS Headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}

def lambda_handler(event, context):
    try:
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Unauthorized'})
            }

        student_id = get_user_id(user)
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        qr_code_string = body.get('qr_code_data')
        qr_data = validate_qr_code_data(qr_code_string)
        if not qr_data:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'invalid/expired QR code'})
            }

        session_id = qr_data['session_id']
        class_id = qr_data['class_id']
        session = get_session(session_id)

        if not session or not session.get('is_active', False):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'session not found or inactive'})
            }

        # 🟢 STEP 1: Calculate material URL early so it's available for 409 and 200
        lecture_material_url = None
        lecture_material_key = session.get('lecture_material_key')
        if lecture_material_key:
            lecture_material_url = get_lecture_material_presigned_url(
                session_id=session_id,
                key=lecture_material_key,
                expiration=86400
            )

        # If student scanned before, return the material URL with a 409
        if check_attendance_exists(session_id, student_id):
            class_data = get_class(class_id)
            return {
                'statusCode': 409,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'message': 'you have already marked attendance for this session',
                    'class_name': class_data.get('class_name') if class_data else 'Class',
                    'scan_timestamp': datetime.utcnow().isoformat(),
                    'download_url': lecture_material_url
                })
            }

        # 🟢 STEP 3: Record new attendance
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
            return {'statusCode': 500, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'failed to record'})}

        # Send SNS notification
        send_attendance_notification(
            student_id=student_id,
            session_id=session_id,
            class_id=class_id,
            message_type='attendance_confirmed',
            lecture_material_url=lecture_material_url,
            lecture_material_key=lecture_material_key
        )

        class_data = get_class(class_id)
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'attendance_id': attendance_id,
                'class_name': class_data.get('class_name') if class_data else None,
                'scan_timestamp': scan_timestamp,
                'download_url': lecture_material_url, # 🟢 Included on success
                'message': 'attendance recorded successfully'
            })
        }

    except Exception as e:
        print(f"Error scanning attendance: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }