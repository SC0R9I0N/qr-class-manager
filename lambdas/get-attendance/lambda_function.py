import json
import os
import sys
import decimal
import boto3  # 🟢 ADDED: For Cognito IDP client

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import (
    get_attendance_by_session, get_attendance_by_student,
    get_session, get_class, get_classes_by_professor
)
import dynamodb_utils
from auth_utils import get_user_from_event, require_professor, require_student, get_user_id

# INITIALIZE COGNITO CLIENT
cognito = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID')

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

def get_email_from_sub(sub):
    """LOOKUP: Fetches email attribute from Cognito User Pool."""
    if not sub:
        return "Unknown"
    try:
        response = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=sub)
        for attr in response['UserAttributes']:
            if attr['Name'] == 'email':
                return attr['Value']
    except Exception as e:
        print(f"Cognito lookup error for {sub}: {str(e)}")
    return sub # Fallback to original ID

def lambda_handler(event, context):
    try:
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Unauthorized'}, default=default_serializer)
            }

        query_params = event.get('queryStringParameters') or {}
        session_id = query_params.get('session_id')
        class_id = query_params.get('class_id')
        student_id = query_params.get('student_id')

        is_professor = require_professor(user)
        is_student = require_student(user)
        user_id = get_user_id(user)

        if is_professor:
            if session_id:
                session = get_session(session_id)
                if not session:
                    return {'statusCode': 404, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'not found'}, default=default_serializer)}

                class_data = get_class(session['class_id'])
                if class_data and class_data.get('professor_id') != user_id:
                    return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'forbidden'}, default=default_serializer)}

                attendance_records = get_attendance_by_session(session_id)

                # ENRICH RECORDS WITH EMAILS
                for record in attendance_records:
                    record['student_email'] = get_email_from_sub(record.get('student_id'))

                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'session_id': session_id,
                        'total_present': len(attendance_records),
                        'attendance_records': attendance_records
                    }, default=default_serializer)
                }

            elif class_id:
                class_data = get_class(class_id)
                if not class_data or class_data.get('professor_id') != user_id:
                    return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'forbidden'}, default=default_serializer)}

                if student_id:
                    attendance_records = get_attendance_by_student(student_id, class_id)
                else:
                    attendance_records = dynamodb_utils.get_attendance_by_class(class_id)

                # ENRICH RECORDS WITH EMAILS
                for record in attendance_records:
                    record['student_email'] = get_email_from_sub(record.get('student_id'))

                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'class_id': class_id,
                        'total_present': len(attendance_records),
                        'attendance_records': attendance_records
                    }, default=default_serializer)
                }

            elif student_id:
                attendance_records = get_attendance_by_student(student_id)
                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'student_id': student_id,
                        'student_email': get_email_from_sub(student_id), # Lookup single student email
                        'total_present': len(attendance_records),
                        'attendance_records': attendance_records
                    }, default=default_serializer)
                }

            else:
                classes = get_classes_by_professor(user_id)
                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({'classes': classes}, default=default_serializer)
                }

        elif is_student:
            attendance_records = get_attendance_by_student(user_id, class_id) if class_id else get_attendance_by_student(user_id)
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({'attendance_records': attendance_records}, default=default_serializer)
            }

        return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'invalid role'}, default=default_serializer)}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'server error'}, default=default_serializer)}