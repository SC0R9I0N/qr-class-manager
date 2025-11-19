import json
import os
import sys
import uuid
from datetime import datetime

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from qr_generator import generate_and_upload_qr_code
from dynamodb_utils import get_session, update_session, get_class
from auth_utils import get_user_from_event, require_professor, get_user_id


def lambda_handler(event, context):
    """
    Expected event body:
    {
        "session_id": "string",
        "expiry_minutes": 60 (optional, default: 60)
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
        
        # user is a professor
        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'only professors can generate QR codes'})
            }
        
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        session_id = body.get('session_id')
        if not session_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'session_id is required'})
            }
        
        # make sure session exists and belongs to professor
        session = get_session(session_id)
        if not session:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'session not found'})
            }
        
        # make sure professor owns the class
        class_data = get_class(session['class_id'])
        if not class_data:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'class not found'})
            }
        
        professor_id = get_user_id(user)
        if class_data.get('professor_id') != professor_id:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'you do not own this class'})
            }
        
        expiry_minutes = body.get('expiry_minutes', 60)
        
        qr_result = generate_and_upload_qr_code(
            session_id=session_id,
            class_id=session['class_id'],
            expiry_minutes=expiry_minutes
        )
        
        if not qr_result.get('qr_code_url'):
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'failed to generate QR code'})
            }
        
        update_session(session_id, {
            'qr_code_url': qr_result['qr_code_url'],
            'qr_code_data': qr_result['qr_code_string'],
            'is_active': True
        })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'session_id': session_id,
                'qr_code_url': qr_result['qr_code_url'],
                'qr_code_data': qr_result['qr_data'],
                'expires_at': qr_result['qr_data'].get('expiry')
            })
        }
    
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

