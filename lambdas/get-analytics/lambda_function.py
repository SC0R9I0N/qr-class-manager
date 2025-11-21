import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from shared import auth_utils
from shared import dynamodb_utils
from shared import models
from shared import qr_generator
from shared import s3_utils
from shared import sns_utils

# add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from dynamodb_utils import (
    get_attendance_by_session, get_sessions_by_class,
    get_class, get_classes_by_professor, get_attendance_by_student, get_session
)
from auth_utils import get_user_from_event, require_professor, get_user_id


def lambda_handler(event, context):
    """
    Query parameters:
    - class_id: Get analytics for a specific class (required for professors)
    - session_id: Get analytics for a specific session (optional)
    """
    try:
        user = get_user_from_event(event)
        if not user:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'unauthorized'})
            }
        
        if not require_professor(user):
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'only professors can see analytics'})
            }
        
        user_id = get_user_id(user)
        
        query_params = event.get('queryStringParameters') or {}
        class_id = query_params.get('class_id')
        session_id = query_params.get('session_id')
        
        if session_id:
            # analytics for a specific session
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
            
            attendance_records = get_attendance_by_session(session_id)
            
            total_students = len(attendance_records)
            present_count = len(attendance_records)
            attendance_rate = (present_count / total_students * 100) if total_students > 0 else 0
            
            # group by time intervals (if needed)
            scan_times = [record.get('scan_timestamp') for record in attendance_records]
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'session_id': session_id,
                    'class_id': session['class_id'],
                    'session_date': session.get('session_date'),
                    'analytics': {
                        'total_students': total_students,
                        'present_count': present_count,
                        'absent_count': total_students - present_count,
                        'attendance_rate': round(attendance_rate, 2),
                        'scan_times': scan_times
                    },
                    'attendance_records': attendance_records
                })
            }
        
        elif class_id:
            # analytics for class (all sessions)
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

            total_sessions = len(sessions)
            session_analytics = []
            student_attendance = defaultdict(int)
            
            for session in sessions:
                attendance_records = get_attendance_by_session(session['session_id'])
                present_count = len(attendance_records)
                
                session_analytics.append({
                    'session_id': session['session_id'],
                    'session_date': session.get('session_date'),
                    'present_count': present_count,
                    'is_active': session.get('is_active', False)
                })
                
                # track per student attendance
                for record in attendance_records:
                    student_attendance[record['student_id']] += 1
            
            # calculate overall statistics
            total_students = len(student_attendance)
            avg_attendance_per_session = sum(s['present_count'] for s in session_analytics) / total_sessions if total_sessions > 0 else 0
            
            student_rates = {
                student_id: (count / total_sessions * 100) if total_sessions > 0 else 0
                for student_id, count in student_attendance.items()
            }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'class_id': class_id,
                    'class_name': class_data.get('class_name'),
                    'analytics': {
                        'total_sessions': total_sessions,
                        'total_students': total_students,
                        'average_attendance_per_session': round(avg_attendance_per_session, 2),
                        'session_analytics': session_analytics,
                        'student_attendance_rates': student_rates
                    }
                })
            }
        
        else:
            # summary for all professor's classes
            classes = get_classes_by_professor(user_id)
            
            class_summaries = []
            for class_item in classes:
                sessions = get_sessions_by_class(class_item['class_id'])
                total_sessions = len(sessions)
                
                total_attendance = 0
                for session in sessions:
                    attendance_records = get_attendance_by_session(session['session_id'])
                    total_attendance += len(attendance_records)
                
                class_summaries.append({
                    'class_id': class_item['class_id'],
                    'class_name': class_item.get('class_name'),
                    'total_sessions': total_sessions,
                    'total_attendance_records': total_attendance
                })
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'message': 'Please specify class_id or session_id for detailed analytics',
                    'classes': class_summaries
                })
            }
    
    except Exception as e:
        print(f"Error getting analytics: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error', 'message': str(e)})
        }

