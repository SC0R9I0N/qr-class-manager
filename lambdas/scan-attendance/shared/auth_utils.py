import os
import json
import boto3
from typing import Optional, Dict
from jose import jwt, JWTError
import urllib.request


# init Cognito client
cognito_client = boto3.client('cognito-idp')
COGNITO_REGION = "us-east-1"
USER_POOL_ID = os.environ.get('USER_POOL_ID', '')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID', '')

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        with urllib.request.urlopen(JWKS_URL) as response:
            _jwks_cache = json.loads(response.read())["keys"]
    return _jwks_cache

def verify_jwt(token):
    try:
        jwks = get_jwks()
        headers = jwt.get_unverified_header(token)
        key = next(k for k in jwks if k["kid"] == headers["kid"])
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"
        )
        return claims
    except (JWTError, StopIteration) as e:
        print(f"[auth_utils] JWT verification failed: {e}")
        return None

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
                raw_groups = claims.get('cognito:groups', '')
                group_list = raw_groups.split(',') if isinstance(raw_groups, str) else raw_groups
                return {
                    'user_id': claims.get('sub'),
                    'email': claims.get('email'),
                    'username': claims.get('cognito:username'),
                    'groups': group_list,
                    'is_professor': 'professors' in group_list,
                    'is_student': 'students' in group_list
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
    """Verify and decode a Cognito JWT using JWKS"""
    try:
        region = os.environ.get("AWS_REGION", "us-east-1")
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

        jwks = get_jwks()

        headers = jwt.get_unverified_header(token)
        key = next(k for k in _jwks_cache if k["kid"] == headers["kid"])

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"https://cognito-idp.{region}.amazonaws.com/{USER_POOL_ID}"
        )
        return claims

    except (JWTError, StopIteration) as e:
        print(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in token verification: {e}")
        return None

#def verify_token(token: str) -> Optional[Dict]:
#    """
#    Arg:
#        token: JWT token string

#    Returns:
#        Decoded token claims or None if invalid
#    """
#    try:
        # get JWKS URL for the user pool
#        jwks_url = f"https://cognito-idp.{os.environ.get('AWS_REGION', 'us-east-1')}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

        # for production, fetch and cache JWKS
        # in production, use jose library with JWKS
        # decode without verification for now but should verify in production
        # TODO: placeholder, implement proper JWKS verification
#        decoded = jwt.get_unverified_claims(token)
#        return decoded
#    except JWTError as e:
#        print(f"Error verifying token: {e}")
#        return None
#    except Exception as e:
#        print(f"Error in token verification: {e}")
#        return None

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