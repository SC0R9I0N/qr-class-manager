import json
import os
import sys
import uuid
from datetime import datetime

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import (
    create_session, get_session, update_session,
    get_sessions_by_class, get_class
)
from auth_utils import get_user_from_event, require_professor, get_user_id


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
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'unauthorized'})
            }
        
        # only professors can manage sessions
        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'only professors can manage sessions'})
            }
        
        user_id = get_user_id(user)
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        
        # GET
        if http_method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            class_id = query_params.get('class_id')
            session_id = query_params.get('session_id')
            
            if session_id:
                # get specific session
                session = get_session(session_id)
                if not session:
                    return {
                        'statusCode': 404,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'session not found'})
                    }
                
                class_data = get_class(session['class_id'])
                if class_data and class_data.get('professor_id') != user_id:
                    return {
                        'statusCode': 403,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'you do not own this class'})
                    }
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(session)
                }
            
            elif class_id:
                # get all sessions for a class
                class_data = get_class(class_id)
                if not class_data:
                    return {
                        'statusCode': 404,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'class not found'})
                    }
                
                if class_data.get('professor_id') != user_id:
                    return {
                        'statusCode': 403,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'you do not own this class'})
                    }
                
                sessions = get_sessions_by_class(class_id)

                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'class_id': class_id,
                        'sessions': sessions,
                        'count': len(sessions)
                    })
                }
            
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'class_id or session_id is required'})
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
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'class_id, session_date, and start_time are required'})
                }
            
            class_data = get_class(class_id)
            if not class_data:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'class not found'})
                }
            
            if class_data.get('professor_id') != user_id:
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'you do not own this class'})
                }
            
            # create session
            session_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            session_data = {
                'session_id': session_id,
                'class_id': class_id,
                'session_date': session_date,
                'start_time': start_time,
                'end_time': end_time,
                'is_active': False,  # QR code not generated yet
                'created_at': created_at
            }
            
            result = create_session(session_data)
            
            if result.get('statusCode') != 200:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'failed to create session'})
                }
            
            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(session_data)
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

            if class_data and class_data.get('professor_id') != user_id:
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'you do not own this class'})
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
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'no fields to update'})
                }
            
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            success = update_session(session_id, updates)
            if not success:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'failed to update session'})
                }
            
            # get updated session
            updated_session = get_session(session_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(updated_session)
            }
        
        # DELETE
        elif http_method == 'DELETE':
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
            
            class_data = get_class(session['class_id'])
            if class_data and class_data.get('professor_id') != user_id:
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'you do not own this class'})
                }
            
            # deactivate session
            success = update_session(session_id, {
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            })
            
            if not success:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'failed to deactivate session'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'session deactivated successfully'})
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'method not allowed'})
            }
    
    except Exception as e:
        print(f"Error managing session: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

