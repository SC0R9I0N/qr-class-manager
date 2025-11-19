import os
import json
import boto3
from typing import Optional, Dict
from jose import jwt, JWTError


# init Cognito client
cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID', '')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID', '')


def get_user_from_event(event: Dict) -> Optional[Dict]:
    """
    Arg:
        event: API Gateway Lambda event
    
    Returns:
        Dictionary with user information or None if not authenticated
    """
    try:
        # check for Cognito authorizer claims
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer'].get('claims', {})
            if claims:
                return {
                    'user_id': claims.get('sub'),
                    'email': claims.get('email'),
                    'username': claims.get('cognito:username'),
                    'groups': claims.get('cognito:groups', []),
                    'is_professor': 'professors' in claims.get('cognito:groups', []),
                    'is_student': 'students' in claims.get('cognito:groups', [])
                }
        
        # fallback: check for identity context (if using IAM authorizer)
        if 'requestContext' in event and 'identity' in event['requestContext']:
            identity = event['requestContext']['identity']
            return {
                'user_id': identity.get('cognitoIdentityId'),
                'source_ip': identity.get('sourceIp')
            }
        
        return None
    except Exception as e:
        print(f"Error extracting user from event: {e}")
        return None


def verify_token(token: str) -> Optional[Dict]:
    """
    Arg:
        token: JWT token string
    
    Returns:
        Decoded token claims or None if invalid
    """
    try:
        # get JWKS URL for the user pool
        jwks_url = f"https://cognito-idp.{os.environ.get('AWS_REGION', 'us-east-1')}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
        
        # for production, fetch and cache JWKS
        # in production, use jose library with JWKS
        # decode without verification for now but should verify in production
        # TODO: placeholder, implement proper JWKS verification
        decoded = jwt.get_unverified_claims(token)
        return decoded
    except JWTError as e:
        print(f"Error verifying token: {e}")
        return None
    except Exception as e:
        print(f"Error in token verification: {e}")
        return None


def require_professor(user: Optional[Dict]) -> bool:
    """
    Arg:
        user: User dictionary from get_user_from_event
    
    Returns:
        True if user is a professor and False otherwise
    """
    if not user:
        return False
    return user.get('is_professor', False)


def require_student(user: Optional[Dict]) -> bool:
    """
    Arg:
        user: User dictionary from get_user_from_event
    
    Returns:
        True if user is a student and False otherwise
    """
    if not user:
        return False
    return user.get('is_student', False)


def get_user_id(user: Optional[Dict]) -> Optional[str]:
    """
    Arg:
        user: User dictionary from get_user_from_event
    
    Returns:
        User ID string or None
    """
    if not user:
        return None
    return user.get('user_id') or user.get('cognitoIdentityId')

