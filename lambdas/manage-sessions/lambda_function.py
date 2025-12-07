import json
import os
import sys
import uuid
from datetime import datetime
import decimal  # 🟢 CRITICAL FIX: Ensure decimal is imported here
from shared import auth_utils
from shared import dynamodb_utils
from shared import models
from shared import qr_generator
from shared import s3_utils
from shared import sns_utils

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import (
    create_session, get_session, update_session,
    get_sessions_by_class, get_class,
    get_attendance_count_by_session
)
from auth_utils import get_user_from_event, require_professor, get_user_id

# Define Universal CORS Headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}

def default_serializer(obj):
    """Serialize DynamoDB types (like Decimal) to JSON compatible types."""
    if isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def lambda_handler(event, context):
    """
    - GET: List sessions (query params: class_id)
    - POST: Create a new session
    - PUT: Update a session
    - DELETE: Deactivate a session
    """
    try:
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'unauthorized'}, default=default_serializer)
            }

        # only professors can manage sessions
        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'only professors can manage sessions'}, default=default_serializer)
            }

        user_id = get_user_id(user)
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')

        # GET
        if http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            class_id = query_params.get('class_id')
            path_params = event.get('pathParameters') or {}
            session_id = path_params.get('session_id') or query_params.get('session_id')

            if session_id:
                # get specific session
                session = get_session(session_id)
                if not session:
                    return {
                        'statusCode': 404,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({'error': 'session not found'}, default=default_serializer)
                    }

                class_data = get_class(session['class_id'])
                if class_data and class_data.get('professor_id') != user_id:
                    return {
                        'statusCode': 403,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({'error': 'you do not own this class'}, default=default_serializer)
                    }

                try:
                    session['attendance_count'] = get_attendance_count_by_session(session_id)
                except:
                    session['attendance_count'] = 0

                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(session, default=default_serializer)
                }

            elif class_id:
                # get all sessions for a class
                class_data = get_class(class_id)
                if not class_data:
                    return {
                        'statusCode': 404,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({'error': 'class not found'}, default=default_serializer)
                    }

                if class_data.get('professor_id') != user_id:
                    return {
                        'statusCode': 403,
                        'headers': CORS_HEADERS,
                        'body': json.dumps({'error': 'you do not own this class'}, default=default_serializer)
                    }

                sessions = get_sessions_by_class(class_id)

                enriched_sessions = []
                for session in sessions:
                    session_id = session['session_id']
                    try:
                        session['attendance_count'] = get_attendance_count_by_session(session_id)
                    except Exception as e:
                        print(f"Error fetching attendance count for {session_id}: {str(e)}")
                        session['attendance_count'] = 0
                    enriched_sessions.append(session)

                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'class_id': class_id,
                        'sessions': enriched_sessions,
                        'count': len(enriched_sessions)
                    }, default=default_serializer)
                }

            else:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'class_id or session_id is required'}, default=default_serializer)
                }

        # POST
        elif http_method == 'POST':
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', {})

            class_id = body.get('class_id')
            session_date = body.get('session_date')
            start_time = body.get('start_time')
            end_time = body.get('end_time')

            if not all([class_id, session_date, start_time]):
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'class_id, session_date, and start_time are required'}, default=default_serializer)
                }

            class_data = get_class(class_id)
            if not class_data:
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'class not found'}, default=default_serializer)
                }

            if class_data.get('professor_id') != user_id:
                return {
                    'statusCode': 403,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'you do not own this class'}, default=default_serializer)
                }

            session_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()

            qr_result = qr_generator.generate_and_upload_qr_code(session_id, class_id)
            qr_code_url = qr_result.get('qr_code_url')

            session_data = {
                'session_id': session_id,
                'class_id': class_id,
                'session_date': session_date,
                'start_time': start_time,
                'end_time': end_time,
                'is_active': bool(qr_code_url),
                'qr_code_url': qr_code_url,
                'created_at': created_at
            }

            result = create_session(session_data)

            if result.get('statusCode') != 200:
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'failed to create session'}, default=default_serializer)
                }

            return {
                'statusCode': 201,
                'headers': CORS_HEADERS,
                'body': json.dumps(session_data, default=default_serializer)
            }

        # PUT
        elif http_method == 'PUT':
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', {})

            session_id = body.get('session_id')
            if not session_id:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'session_id is required'}, default=default_serializer)
                }

            session = get_session(session_id)

            if not session:
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'session not found'}, default=default_serializer)
                }

            class_data = get_class(session['class_id'])

            if class_data and class_data.get('professor_id') != user_id:
                return {
                    'statusCode': 403,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'you do not own this class'}, default=default_serializer)
                }

            updates = {}
            if 'session_date' in body:
                updates['session_date'] = body['session_date']
            if 'start_time' in body:
                updates['start_time'] = body['start_time']
            if 'end_time' in body:
                updates['end_time'] = body['end_time']
            if 'is_active' in body:
                updates['is_active'] = body['is_active']

            if not updates:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'no fields to update'}, default=default_serializer)
                }

            updates['updated_at'] = datetime.utcnow().isoformat()

            success = update_session(session_id, updates)
            if not success:
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'failed to update session'}, default=default_serializer)
                }

            updated_session = get_session(session_id)
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps(updated_session, default=default_serializer)
            }

        # DELETE
        elif http_method == 'DELETE':
            query_params = event.get('queryStringParameters') or {}
            session_id = query_params.get('session_id')

            if not session_id:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'session_id is required'}, default=default_serializer)
                }

            session = get_session(session_id)
            if not session:
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'session not found'}, default=default_serializer)
                }

            class_data = get_class(session['class_id'])
            if class_data and class_data.get('professor_id') != user_id:
                return {
                    'statusCode': 403,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'you do not own this class'}, default=default_serializer)
                }

            success = update_session(session_id, {
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            })

            if not success:
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'error': 'failed to deactivate session'}, default=default_serializer)
                }

            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'message': 'session deactivated successfully'}, default=default_serializer)
            }

        else:
            return {
                'statusCode': 405,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'method not allowed'}, default=default_serializer)
            }

    except Exception as e:
        print(f"Error managing session: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'internal server error', 'message': str(e)}, default=default_serializer)
        }