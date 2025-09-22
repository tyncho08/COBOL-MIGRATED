"""
Authentication Router
Handles user login, logout, and token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
from pydantic import BaseModel

from app.config.database import get_db
from app.config.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    PermissionLevel,
    ModuleCode
)
from app.models import User
from app.schemas.auth import Token, TokenData, UserLogin, UserResponse, PasswordChange

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def require_permission(module: str, level: int):
    """Decorator factory for permission checking"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if current_user.is_superuser:
            return current_user
            
        user_level = current_user.module_access.get(module, 0)
        if user_level < level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {module} module"
            )
        return current_user
    return permission_checker


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """User login - returns access and refresh tokens"""
    # Authenticate user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.now()
    user.login_count = (user.login_count or 0) + 1
    user.last_activity = datetime.now()
    db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(request: dict, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    refresh_token_str = request.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    payload = decode_token(refresh_token_str)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,  # Return same refresh token
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        user_level=current_user.user_level,
        module_access=current_user.module_access or {},
        allowed_companies=current_user.allowed_companies or [],
    )


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Verify new password confirmation
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user - update last activity"""
    current_user.last_activity = datetime.now()
    db.commit()
    
    return {"message": "Successfully logged out"}


# Permission checking utilities
@router.get("/permissions")
def get_user_permissions(current_user: User = Depends(get_current_user)):
    """Get user module permissions"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_superuser": current_user.is_superuser,
        "user_level": current_user.user_level,
        "module_access": current_user.module_access or {},
        "permissions": {
            "sales": {
                "level": current_user.module_access.get(ModuleCode.SALES, 0),
                "can_view": current_user.module_access.get(ModuleCode.SALES, 0) >= PermissionLevel.ENQUIRY,
                "can_edit": current_user.module_access.get(ModuleCode.SALES, 0) >= PermissionLevel.OPERATOR,
                "can_delete": current_user.module_access.get(ModuleCode.SALES, 0) >= PermissionLevel.SUPERVISOR,
                "can_close": current_user.module_access.get(ModuleCode.SALES, 0) >= PermissionLevel.MANAGER,
            },
            "purchase": {
                "level": current_user.module_access.get(ModuleCode.PURCHASE, 0),
                "can_view": current_user.module_access.get(ModuleCode.PURCHASE, 0) >= PermissionLevel.ENQUIRY,
                "can_edit": current_user.module_access.get(ModuleCode.PURCHASE, 0) >= PermissionLevel.OPERATOR,
                "can_delete": current_user.module_access.get(ModuleCode.PURCHASE, 0) >= PermissionLevel.SUPERVISOR,
                "can_close": current_user.module_access.get(ModuleCode.PURCHASE, 0) >= PermissionLevel.MANAGER,
            },
            "stock": {
                "level": current_user.module_access.get(ModuleCode.STOCK, 0),
                "can_view": current_user.module_access.get(ModuleCode.STOCK, 0) >= PermissionLevel.ENQUIRY,
                "can_edit": current_user.module_access.get(ModuleCode.STOCK, 0) >= PermissionLevel.OPERATOR,
                "can_delete": current_user.module_access.get(ModuleCode.STOCK, 0) >= PermissionLevel.SUPERVISOR,
                "can_close": current_user.module_access.get(ModuleCode.STOCK, 0) >= PermissionLevel.MANAGER,
            },
            "general": {
                "level": current_user.module_access.get(ModuleCode.GENERAL, 0),
                "can_view": current_user.module_access.get(ModuleCode.GENERAL, 0) >= PermissionLevel.ENQUIRY,
                "can_edit": current_user.module_access.get(ModuleCode.GENERAL, 0) >= PermissionLevel.OPERATOR,
                "can_delete": current_user.module_access.get(ModuleCode.GENERAL, 0) >= PermissionLevel.SUPERVISOR,
                "can_close": current_user.module_access.get(ModuleCode.GENERAL, 0) >= PermissionLevel.MANAGER,
            },
            "system": {
                "level": current_user.module_access.get(ModuleCode.SYSTEM, 0),
                "can_view": current_user.module_access.get(ModuleCode.SYSTEM, 0) >= PermissionLevel.ENQUIRY,
                "can_edit": current_user.module_access.get(ModuleCode.SYSTEM, 0) >= PermissionLevel.OPERATOR,
                "can_delete": current_user.module_access.get(ModuleCode.SYSTEM, 0) >= PermissionLevel.SUPERVISOR,
                "can_admin": current_user.module_access.get(ModuleCode.SYSTEM, 0) >= PermissionLevel.ADMIN,
            },
        }
    }