import json
import os
import sys
from shared import auth_utils
from shared import dynamodb_utils
from shared import models
from shared import qr_generator
from shared import s3_utils
from shared import sns_utils

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import (
    get_attendance_by_session, get_attendance_by_student,
    get_session, get_class, get_classes_by_professor
)
from auth_utils import get_user_from_event, require_professor, require_student, get_user_id


def lambda_handler(event, context):
    """
    Query parameters:
    - session_id: Get attendance for a specific session (professors only)
    - class_id: Get attendance for a class (professors) or student's attendance in a class
    - student_id: Get attendance for a specific student (professors only)
    """
    try:
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        query_params = event.get('queryStringParameters') or {}
        session_id = query_params.get('session_id')
        class_id = query_params.get('class_id')
        student_id = query_params.get('student_id')
        
        is_professor = require_professor(user)
        is_student = require_student(user)
        user_id = get_user_id(user)
        
        # profs can view attendance by session, class, or student
        if is_professor:
            if session_id:
                session = get_session(session_id)
                if not session:
                    return {
                        'statusCode': 404,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'session not found'})
                    }
                
                # professor owns the class
                class_data = get_class(session['class_id'])
                if class_data and class_data.get('professor_id') != user_id:
                    return {
                        'statusCode': 403,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'you do not own this class'})
                    }
                
                attendance_records = get_attendance_by_session(session_id)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'session_id': session_id,
                        'class_id': session['class_id'],
                        'attendance_count': len(attendance_records),
                        'attendance': attendance_records
                    })
                }
            
            elif class_id:
                # get all attendance for a class
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
                
                # if student_id is given, get that student's attendance in the class
                if student_id:
                    attendance_records = get_attendance_by_student(student_id, class_id)
                else:
                    # TODO would need a different query
                    # get all attendance for the class (would need a different query)
                    # for now return empty, might need a GSI for class_id in attendance table
                    attendance_records = []
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'class_id': class_id,
                        'student_id': student_id if student_id else None,
                        'attendance_count': len(attendance_records),
                        'attendance': attendance_records
                    })
                }
            
            elif student_id:
                # get all attendance for a specific student
                attendance_records = get_attendance_by_student(student_id)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'student_id': student_id,
                        'attendance_count': len(attendance_records),
                        'attendance': attendance_records
                    })
                }
            
            else:
                # get all classes for professor and their attendance summary
                classes = get_classes_by_professor(user_id)
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'message': 'please specify session_id, class_id, or student_id',
                        'classes': classes
                    })
                }
        
        # students can only view their own attendance
        elif is_student:
            if class_id:
                attendance_records = get_attendance_by_student(user_id, class_id)
            else:
                attendance_records = get_attendance_by_student(user_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'student_id': user_id,
                    'class_id': class_id if class_id else None,
                    'attendance_count': len(attendance_records),
                    'attendance': attendance_records
                })
            }
        
        else:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'invalid user role'})
            }
    
    except Exception as e:
        print(f"Error getting attendance: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

