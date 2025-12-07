import json
import os
import sys
import uuid
import time
from datetime import datetime
from shared import auth_utils
from shared import dynamodb_utils
from shared import models
from shared import qr_generator
from shared import s3_utils
from shared import sns_utils

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from qr_generator import generate_and_upload_qr_code
from dynamodb_utils import get_class, create_session, update_session
from auth_utils import get_user_from_event, require_professor, get_user_id

# Define Universal CORS Headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}


def lambda_handler(event, context):
    """
    Handles creating a new session for a class and generating a corresponding QR code.
    Triggered by POST /sessions/{session_id}/generate-qr (where session_id is class_id)
    """
    try:
        # 1. Authentication Check
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Unauthorized'})
            }

        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Only professors can generate QR codes'})
            }

        # 2. Extract Class ID from path parameters
        # In CDK, this is mapped from the {session_id} placeholder
        path_parameters = event.get('pathParameters') or {}
        class_id = path_parameters.get('session_id')

        if not class_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Class ID is missing in path parameters'})
            }

        # 3. Ownership and Existence Checks
        class_data = get_class(class_id)
        if not class_data:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Class not found'})
            }

        professor_id = get_user_id(user)
        if class_data.get('professor_id') != professor_id:
            return {
                'statusCode': 403,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'You do not own this class'})
            }

        # 4. Create New Session Entry
        new_session_id = str(uuid.uuid4())

        # Formatting friendly date and time for the session title
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        title = f"{class_data.get('class_name', 'Session')} - {date_str} {time_str}"

        session_input = {
            'session_id': new_session_id,
            'class_id': class_id,
            'session_date': date_str,
            'start_time': time_str,
            'title': title,
            'is_active': True,
        }

        # Save placeholder session to DynamoDB
        create_session(session_input)

        # 5. Generate and Upload QR Code
        # We use a default expiry of 60 minutes for generated codes
        expiry_minutes = 60

        qr_result = generate_and_upload_qr_code(
            session_id=new_session_id,
            class_id=class_id,
            expiry_minutes=expiry_minutes
        )

        if not qr_result.get('qr_code_url'):
            # Log failure but the session record stays (or implement cleanup here)
            print(f"Failed to generate QR code for new session {new_session_id}.")
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Failed to generate QR code image'})
            }

        # 6. Update Session with QR metadata
        update_session(new_session_id, {
            'qr_code_url': qr_result['qr_code_url'],
            'qr_code_data': qr_result['qr_code_string'],
            'is_active': True
        })

        # 7. Return Successful Response
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'session_id': new_session_id,
                'qr_code_url': qr_result['qr_code_url'],
                'qr_data': qr_result['qr_code_string'],  # Backend matches frontend key expectation
                'title': title
            })
        }

    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }