import os
import json
import qrcode
import boto3
from io import BytesIO
from typing import Dict, Optional
from datetime import datetime, timedelta
import uuid


# init S3 client
s3_client = boto3.client('s3')
S3_BUCKET = os.environ.get('QR_CODE_BUCKET', 'qr-class-manager-qrcodes')


def generate_qr_code_data(session_id: str, class_id: str, expiry_minutes: int = 60) -> Dict:
    """
    Args:
        session_id: Unique session identifier
        class_id: Class identifier
        expiry_minutes: Minutes until QR code expires (default: 60)
    
    Returns:
        Dictionary containing QR code data
    """

    timestamp = datetime.utcnow().isoformat()
    expiry = (datetime.utcnow() + timedelta(minutes=expiry_minutes)).isoformat()
    
    return {
        'session_id': session_id,
        'class_id': class_id,
        'timestamp': timestamp,
        'expiry': expiry
    }


def create_qr_code_image(qr_data: Dict) -> BytesIO:
    """
    Arg:
        qr_data: Dictionary containing QR code data
    
    Returns:
        BytesIO object containing PNG image data
    """
    qr_string = json.dumps(qr_data)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes


def upload_qr_code_to_s3(session_id: str, qr_image: BytesIO) -> Optional[str]:
    """
    Args:
        session_id: Session identifier (used as filename)
        qr_image: BytesIO object containing PNG image
    
    Returns:
        S3 URL of uploaded image, or None if upload fails
    """
    try:
        key = f"qrcodes/{session_id}.png"
        
        s3_client.upload_fileobj(
            qr_image,
            S3_BUCKET,
            key,
            ExtraArgs={'ContentType': 'image/png'}
        )
        
        # generate public URL (or use CloudFront URL if configured)
        cloudfront_domain = os.environ.get('CLOUDFRONT_DOMAIN')
        if cloudfront_domain:
            url = f"https://{cloudfront_domain}/{key}"
        else:
            url = f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"

        print(f"[qr_generator] QR code uploaded to: {url}")
        
        return url
    except Exception as e:
        print(f"Error uploading QR code to S3: {e}")
        return None


def generate_and_upload_qr_code(session_id: str, class_id: str, expiry_minutes: int = 60) -> Dict:
    """
    Args:
        session_id: Unique session identifier
        class_id: Class identifier
        expiry_minutes: Minutes until QR code expires
    
    Returns:
        Dictionary containing qr_data and qr_code_url
    """
    qr_data = generate_qr_code_data(session_id, class_id, expiry_minutes)
    
    qr_image = create_qr_code_image(qr_data)
    
    qr_code_url = upload_qr_code_to_s3(session_id, qr_image)
    
    return {
        'qr_data': qr_data,
        'qr_code_url': qr_code_url,
        'qr_code_string': json.dumps(qr_data)
    }


def validate_qr_code_data(qr_string: str) -> Optional[Dict]:
    """
    Arg:
        qr_string: JSON string from scanned QR code
    
    Returns:
        Parsed QR code data if valid or None otherwise
    """
    try:
        qr_data = json.loads(qr_string)
        
        required_fields = ['session_id', 'class_id', 'timestamp']
        if not all(field in qr_data for field in required_fields):
            return None
        
        if 'expiry' in qr_data:
            expiry_time = datetime.fromisoformat(qr_data['expiry'])
            if datetime.utcnow() > expiry_time:
                return None
        
        return qr_data
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error validating QR code data: {e}")
        return None