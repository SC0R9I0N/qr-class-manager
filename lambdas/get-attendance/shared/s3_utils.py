import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError


# init S3 client
s3_client = boto3.client('s3')
QR_CODE_BUCKET = os.environ.get('QR_CODE_BUCKET', 'qr-class-manager-qrcodes')


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

