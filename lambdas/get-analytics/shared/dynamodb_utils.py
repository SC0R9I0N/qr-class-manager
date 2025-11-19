import os
import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
from decimal import Decimal

# init DynamoDB client
dynamodb = boto3.resource('dynamodb')

# table names from environment variables
CLASSES_TABLE = os.environ.get('CLASSES_TABLE', 'classes')
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'sessions')
ATTENDANCE_TABLE = os.environ.get('ATTENDANCE_TABLE', 'attendance')

def get_table(table_name: str):
    return dynamodb.Table(table_name)


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def serialize_item(item: Dict) -> Dict:
    return json.loads(json.dumps(item, default=decimal_default))


def create_class(class_data: Dict) -> Dict:
    table = get_table(CLASSES_TABLE)
    try:
        response = table.put_item(Item=class_data)
        return {'statusCode': 200, 'body': serialize_item(class_data)}
    except ClientError as e:
        return {'statusCode': 500, 'error': str(e)}


def get_class(class_id: str) -> Optional[Dict]:
    table = get_table(CLASSES_TABLE)
    try:
        response = table.get_item(Key={'class_id': class_id})
        return serialize_item(response['Item']) if 'Item' in response else None
    except ClientError as e:
        print(f"Error getting class: {e}")
        return None


def get_classes_by_professor(professor_id: str) -> List[Dict]:
    table = get_table(CLASSES_TABLE)
    try:
        response = table.query(
            IndexName='professor_id-index',
            KeyConditionExpression='professor_id = :prof_id',
            ExpressionAttributeValues={':prof_id': professor_id}
        )
        return [serialize_item(item) for item in response.get('Items', [])]
    except ClientError as e:
        print(f"Error querying classes: {e}")
        return []


def create_session(session_data: Dict) -> Dict:
    table = get_table(SESSIONS_TABLE)
    try:
        response = table.put_item(Item=session_data)
        return {'statusCode': 200, 'body': serialize_item(session_data)}
    except ClientError as e:
        return {'statusCode': 500, 'error': str(e)}


def get_session(session_id: str) -> Optional[Dict]:
    table = get_table(SESSIONS_TABLE)
    try:
        response = table.get_item(Key={'session_id': session_id})
        return serialize_item(response['Item']) if 'Item' in response else None
    except ClientError as e:
        print(f"Error getting session: {e}")
        return None


def get_sessions_by_class(class_id: str) -> List[Dict]:
    table = get_table(SESSIONS_TABLE)
    try:
        response = table.query(
            IndexName='class_id-index',
            KeyConditionExpression='class_id = :cid',
            ExpressionAttributeValues={':cid': class_id}
        )
        return [serialize_item(item) for item in response.get('Items', [])]
    except ClientError as e:
        print(f"Error querying sessions: {e}")
        return []


def update_session(session_id: str, updates: Dict) -> bool:
    table = get_table(SESSIONS_TABLE)
    try:
        update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expression_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        return True
    except ClientError as e:
        print(f"Error updating session: {e}")
        return False


def create_attendance(attendance_data: Dict) -> Dict:
    table = get_table(ATTENDANCE_TABLE)
    try:
        response = table.put_item(Item=attendance_data)
        return {'statusCode': 200, 'body': serialize_item(attendance_data)}
    except ClientError as e:
        return {'statusCode': 500, 'error': str(e)}


def get_attendance_by_session(session_id: str) -> List[Dict]:
    table = get_table(ATTENDANCE_TABLE)
    try:
        response = table.query(
            IndexName='session_id-index',
            KeyConditionExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        return [serialize_item(item) for item in response.get('Items', [])]
    except ClientError as e:
        print(f"Error querying attendance: {e}")
        return []


def get_attendance_by_student(student_id: str, class_id: Optional[str] = None) -> List[Dict]:
    table = get_table(ATTENDANCE_TABLE)
    try:
        if class_id:
            response = table.query(
                IndexName='student_class-index',
                KeyConditionExpression='student_id = :sid AND class_id = :cid',
                ExpressionAttributeValues={':sid': student_id, ':cid': class_id}
            )
        else:
            response = table.query(
                IndexName='student_id-index',
                KeyConditionExpression='student_id = :sid',
                ExpressionAttributeValues={':sid': student_id}
            )
        return [serialize_item(item) for item in response.get('Items', [])]
    except ClientError as e:
        print(f"Error querying attendance: {e}")
        return []


def check_attendance_exists(session_id: str, student_id: str) -> bool:
    # check if a student has already marked attendance for a session
    table = get_table(ATTENDANCE_TABLE)
    try:
        response = table.query(
            IndexName='session_student-index',
            KeyConditionExpression='session_id = :sid AND student_id = :stid',
            ExpressionAttributeValues={':sid': session_id, ':stid': student_id},
            Limit=1
        )
        return len(response.get('Items', [])) > 0
    except ClientError as e:
        print(f"Error checking attendance: {e}")
        return False

