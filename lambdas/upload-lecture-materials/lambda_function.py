import json
import os
import sys
import base64
from datetime import datetime

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import get_session, update_session, get_class
from auth_utils import get_user_from_event, require_professor, get_user_id
from s3_utils import upload_lecture_material, delete_lecture_material

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

        # Verify Professor Role
        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Only professors can upload lecture materials'})
            }

        professor_id = get_user_id(user)

        # Body parsing for standard JSON payload
        body = {}
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        elif event.get('body'):
            body = event['body']

        session_id = body.get('session_id')
        file_content_b64 = body.get('file_content')
        filename = body.get('filename', 'lecture_materials.zip')

        if not session_id or not file_content_b64:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'session_id and file_content are required'})
            }

        # Existence and Ownership Checks
        session = get_session(session_id)
        if not session:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'session not found'})
            }

        class_data = get_class(session['class_id'])
        if not class_data or class_data.get('professor_id') != professor_id:
            return {
                'statusCode': 403,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'you do not own this class'})
            }

        # Decoding base64 to binary for S3 upload
        try:
            file_content = base64.b64decode(file_content_b64)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'invalid base64 content'})
            }

        # Size constraint check (50MB)
        if len(file_content) > 50 * 1024 * 1024:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'file exceeds 50MB limit'})
            }

        # Cleanup existing file
        existing_key = session.get('lecture_material_key')
        if existing_key:
            delete_lecture_material(existing_key)

        # Upload binary to S3
        s3_key = upload_lecture_material(session_id, file_content, filename)

        if not s3_key:
            return {
                'statusCode': 500,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'failed to upload lecture material to s3'})
            }

        # Update Session Table with the new key
        update_session(session_id, {
            'lecture_material_key': s3_key,
            'updated_at': datetime.utcnow().isoformat()
        })

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'session_id': session_id,
                'lecture_material_key': s3_key,
                'message': 'lecture material uploaded successfully'
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }