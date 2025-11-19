import os
import json
import boto3
from typing import Dict, Optional
from botocore.exceptions import ClientError

# init SNS client
sns_client = boto3.client('sns')
ATTENDANCE_TOPIC_ARN = os.environ.get('ATTENDANCE_TOPIC_ARN', '')


def send_attendance_notification(student_id: str, session_id: str, class_id: str, 
                                 message_type: str = 'attendance_confirmed') -> bool:
    """
    Args:
        student_id: Student identifier
        session_id: Session identifier
        class_id: Class identifier
        message_type: Type of notification
    
    Returns:
        True if successful or False otherwise
    """
    if not ATTENDANCE_TOPIC_ARN:
        print("ATTENDANCE_TOPIC_ARN not configured, skipping notification")
        return False
    
    try:
        message = {
            'message_type': message_type,
            'student_id': student_id,
            'session_id': session_id,
            'class_id': class_id,
            'timestamp': json.dumps({})
        }
        
        response = sns_client.publish(
            TopicArn=ATTENDANCE_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f'Attendance {message_type.replace("_", " ").title()}'
        )
        
        return response.get('MessageId') is not None
    except ClientError as e:
        print(f"Error sending SNS notification: {e}")
        return False


def send_bulk_notification(message: Dict, topic_arn: Optional[str] = None) -> bool:
    """
    Args:
        message: Message dictionary to send
        topic_arn: SNS topic ARN (uses default if not provided)
    
    Returns:
        True if successful or False otherwise
    """
    topic = topic_arn or ATTENDANCE_TOPIC_ARN
    if not topic:
        print("No SNS topic ARN configured")
        return False
    
    try:
        response = sns_client.publish(
            TopicArn=topic,
            Message=json.dumps(message)
        )
        return response.get('MessageId') is not None
    except ClientError as e:
        print(f"Error sending SNS notification: {e}")
        return False

