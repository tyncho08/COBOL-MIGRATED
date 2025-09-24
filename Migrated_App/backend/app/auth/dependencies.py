"""
Authentication dependencies for ACAS Migrated API
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# JWT settings from app configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate JWT token and return current user info
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token - this will automatically check expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Return user info from token
        return {
            "username": payload.get("sub"),
            "name": payload.get("name"),
            "role": payload.get("role"),
            "access_level": payload.get("access_level")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_permission(access_level: int = 1):
    """
    Dependency to require specific access level
    """
    def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_level = current_user.get("access_level", 0)
        if user_level < access_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access level {access_level} required, you have level {user_level}"
            )
        return current_user
    return permission_checker

# Pre-defined permission levels
require_read = require_permission(1)    # Basic read access
require_write = require_permission(3)   # Write access
require_approve = require_permission(5) # Approval access
require_admin = require_permission(9)   # Admin access