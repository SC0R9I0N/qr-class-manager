import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError
from io import BytesIO
import base64


# init S3 client
s3_client = boto3.client('s3')
QR_CODE_BUCKET = os.environ.get('QR_CODE_BUCKET', 'qr-class-manager-qrcodes')
LECTURE_MATERIALS_BUCKET = os.environ.get('LECTURE_MATERIALS_BUCKET', 'qr-class-manager-lectures')


def get_presigned_url(bucket: str, key: str, expiration: int = 3600) -> Optional[str]:
    """
    Args:
        bucket: S3 bucket name
        key: S3 object key
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Presigned URL string or None if error
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None


def delete_object(bucket: str, key: str) -> bool:
    """
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        True if successful or False otherwise
    """
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        print(f"Error deleting S3 object: {e}")
        return False


def upload_lecture_material(session_id: str, file_content: bytes, filename: str) -> Optional[str]:
    """
    Args:
        session_id: Session identifier
        file_content: Binary content of the file
        filename: Original filename
    
    Returns:
        S3 key of uploaded file or None if upload fails
    """
    try:
        if not filename.lower().endswith('.zip'):
            filename = f"{filename}.zip"
        
        key = f"lectures/{session_id}/{filename}"
        
        s3_client.put_object(
            Bucket=LECTURE_MATERIALS_BUCKET,
            Key=key,
            Body=file_content,
            ContentType='application/zip'
        )
        
        return key
    except ClientError as e:
        print(f"Error uploading lecture material: {e}")
        return None


def get_lecture_material_presigned_url(session_id: str, key: Optional[str] = None, expiration: int = 3600) -> Optional[str]:
    """
    Args:
        session_id: Session identifier
        key: S3 key (if None, will try to find the material for this session)
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Presigned URL string or None if error
    """
    try:
        if not key:
            # try to find the lecture material for this session, assumes the key is stored in the session record
            # use a standard pattern for now
            key = f"lectures/{session_id}/lecture_materials.zip"
        
        return get_presigned_url(LECTURE_MATERIALS_BUCKET, key, expiration)
    except Exception as e:
        print(f"error getting lecture material presigned URL: {e}")
        return None


def delete_lecture_material(key: str) -> bool:
    """
    Arg:
        key: S3 object key
    
    Returns:
        True if successful or False otherwise
    """
    return delete_object(LECTURE_MATERIALS_BUCKET, key)

