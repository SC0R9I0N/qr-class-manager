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


def lambda_handler(event, context):
    """
    Expected event body (base64 encoded):
    {
        "session_id": "string",
        "file_content": "base64 encoded file content",
        "filename": "lecture_materials.zip"
    }
    
    or through API Gateway with multipart/form-data handled by API Gateway
    """
    try:
        user = get_user_from_event(event)

        if not user:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'only professors can upload lecture materials'})
            }
        
        professor_id = get_user_id(user)
        
        if isinstance(event.get('body'), str):
            if event.get('isBase64Encoded', False):
                body = json.loads(base64.b64decode(event['body']).decode('utf-8'))
            else:
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
        
        session = get_session(session_id)
        if not session:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'session not found'})
            }
        
        class_data = get_class(session['class_id'])
        if not class_data:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'class not found'})
            }
        
        if class_data.get('professor_id') != professor_id:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'you do not own this class'})
            }
        
        file_content_b64 = body.get('file_content')
        filename = body.get('filename', 'lecture_materials.zip')
        
        if not file_content_b64:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'file_content is required (base64 encoded)'})
            }
        
        try:
            file_content = base64.b64decode(file_content_b64)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'invalid base64 file content', 'message': str(e)})
            }
        
        max_size = 50 * 1024 * 1024  # 50MB

        if len(file_content) > max_size:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'file size exceeds maximum of {max_size / (1024*1024)}MB'})
            }
        
        # delete existing lecture material if any
        existing_key = session.get('lecture_material_key')
        if existing_key:
            delete_lecture_material(existing_key)
        
        s3_key = upload_lecture_material(session_id, file_content, filename)
        
        if not s3_key:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'failed to upload lecture material'})
            }
        
        update_session(session_id, {
            'lecture_material_key': s3_key,
            'lecture_material_url': f"s3://{os.environ.get('LECTURE_MATERIALS_BUCKET', 'qr-class-manager-lectures')}/{s3_key}",
            'updated_at': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'session_id': session_id,
                'lecture_material_key': s3_key,
                'filename': filename,
                'file_size': len(file_content),
                'message': 'lecture material uploaded successfully'
            })
        }
    
    except Exception as e:
        print(f"Error uploading lecture material: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

