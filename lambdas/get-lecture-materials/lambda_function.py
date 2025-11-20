import json
import os
import sys

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import get_session, check_attendance_exists, get_class
from auth_utils import get_user_from_event, require_student, get_user_id
from s3_utils import get_lecture_material_presigned_url


def lambda_handler(event, context):
    """
    Query parameters:
    - session_id: Session identifier (required)
    """
    try:
        user = get_user_from_event(event)

        if not user:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        if not require_student(user):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'only students can download lecture materials'})
            }
        
        student_id = get_user_id(user)

        if not student_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'unable to identify student'})
            }
        
        query_params = event.get('queryStringParameters') or {}
        session_id = query_params.get('session_id')
        
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
        
        # make sure student has marked attendance for this session
        if not check_attendance_exists(session_id, student_id):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'you must mark attendance before downloading lecture materials'
                })
            }
        
        lecture_material_key = session.get('lecture_material_key')

        if not lecture_material_key:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'no lecture materials available for this session'})
            }
        
        # generate presigned URL (valid for 1 hour)
        presigned_url = get_lecture_material_presigned_url(
            session_id=session_id,
            key=lecture_material_key,
            expiration=3600
        )
        
        if not presigned_url:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'failed to generate download URL'})
            }
        
        class_data = get_class(session['class_id'])
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'session_id': session_id,
                'class_id': session['class_id'],
                'class_name': class_data.get('class_name') if class_data else None,
                'session_date': session.get('session_date'),
                'download_url': presigned_url,
                'expires_in': 3600,
                'message': 'download URL generated successfully'
            })
        }
    
    except Exception as e:
        print(f"Error getting lecture materials: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

