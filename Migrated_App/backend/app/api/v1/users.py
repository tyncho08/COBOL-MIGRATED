"""
User Management API Endpoints
Handles user administration, permissions, and account management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date
from pydantic import BaseModel

from app.config.database import get_db
from app.models import User
from app.services.user_service import UserService
from app.routers.auth import get_current_user, require_permission
from app.config.security import PermissionLevel, ModuleCode
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


# Request/Response Schemas
class UserCreate(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    user_level: int = 1
    module_access: Optional[Dict[str, int]] = None
    is_superuser: bool = False
    allowed_companies: Optional[List[str]] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    user_level: Optional[int] = None
    module_access: Optional[Dict[str, int]] = None
    is_superuser: Optional[bool] = None
    allowed_companies: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: Optional[str] = None  # Optional for admin changes
    new_password: str


class PermissionUpdate(BaseModel):
    module_access: Dict[str, int]


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int


# Endpoints
@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.ENQUIRY)),
    db: Session = Depends(get_db)
):
    """List users with filtering and pagination"""
    
    service = UserService(db)
    skip = (page - 1) * page_size
    
    users = service.list_users(
        skip=skip,
        limit=page_size,
        is_active=is_active,
        search=search
    )
    
    # Get total count
    total_count = len(service.list_users(is_active=is_active, search=search))
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.ENQUIRY)),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    
    service = UserService(db)
    user = service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.post("", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.OPERATOR)),
    db: Session = Depends(get_db)
):
    """Create new user"""
    
    service = UserService(db)
    
    user = service.create_user(
        username=user_data.username,
        full_name=user_data.full_name,
        email=user_data.email,
        password=user_data.password,
        user_level=user_data.user_level,
        module_access=user_data.module_access,
        is_superuser=user_data.is_superuser,
        allowed_companies=user_data.allowed_companies,
        created_by_user_id=current_user.id
    )
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.OPERATOR)),
    db: Session = Depends(get_db)
):
    """Update user"""
    
    service = UserService(db)
    
    user = service.update_user(
        user_id=user_id,
        full_name=user_data.full_name,
        email=user_data.email,
        user_level=user_data.user_level,
        module_access=user_data.module_access,
        is_superuser=user_data.is_superuser,
        allowed_companies=user_data.allowed_companies,
        is_active=user_data.is_active,
        updated_by_user_id=current_user.id
    )
    
    return UserResponse.from_orm(user)


@router.post("/{user_id}/password")
def change_user_password(
    user_id: int,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Check permissions
    if user_id != current_user.id:
        # Changing another user's password requires admin permissions
        if not current_user.is_superuser and current_user.module_access.get(ModuleCode.SYSTEM, 0) < PermissionLevel.SUPERVISOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to change other user's password"
            )
    
    service = UserService(db)
    
    service.change_password(
        user_id=user_id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
        changed_by_user_id=current_user.id
    )
    
    return {"message": "Password changed successfully"}


@router.post("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.SUPERVISOR)),
    db: Session = Depends(get_db)
):
    """Deactivate user account"""
    
    # Prevent deactivating yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    service = UserService(db)
    user = service.deactivate_user(user_id, current_user.id)
    
    return {"message": f"User {user.username} deactivated successfully"}


@router.post("/{user_id}/activate")
def activate_user(
    user_id: int,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.SUPERVISOR)),
    db: Session = Depends(get_db)
):
    """Activate user account"""
    
    service = UserService(db)
    user = service.activate_user(user_id, current_user.id)
    
    return {"message": f"User {user.username} activated successfully"}


@router.put("/{user_id}/permissions")
def update_user_permissions(
    user_id: int,
    permission_data: PermissionUpdate,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.MANAGER)),
    db: Session = Depends(get_db)
):
    """Update user module permissions"""
    
    service = UserService(db)
    user = service.update_user_permissions(
        user_id=user_id,
        module_access=permission_data.module_access,
        updated_by_user_id=current_user.id
    )
    
    return {"message": f"Permissions updated for user {user.username}"}


@router.get("/{user_id}/activity")
def get_user_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.ENQUIRY)),
    db: Session = Depends(get_db)
):
    """Get user activity history"""
    
    service = UserService(db)
    activity = service.get_user_activity(user_id, days)
    
    return {
        "user_id": user_id,
        "days": days,
        "activities": activity
    }


@router.get("/statistics/summary")
def get_user_statistics(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: User = Depends(require_permission(ModuleCode.SYSTEM, PermissionLevel.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    
    service = UserService(db)
    stats = service.get_user_statistics(from_date, to_date)
    
    return stats


# Permission reference endpoints
@router.get("/permissions/reference")
def get_permission_reference():
    """Get permission levels and module codes reference"""
    
    return {
        "permission_levels": {
            "NONE": PermissionLevel.NONE,
            "ENQUIRY": PermissionLevel.ENQUIRY,
            "OPERATOR": PermissionLevel.OPERATOR,
            "SUPERVISOR": PermissionLevel.SUPERVISOR,
            "MANAGER": PermissionLevel.MANAGER,
            "ADMIN": PermissionLevel.ADMIN,
        },
        "module_codes": {
            "SALES": ModuleCode.SALES,
            "PURCHASE": ModuleCode.PURCHASE,
            "STOCK": ModuleCode.STOCK,
            "GENERAL": ModuleCode.GENERAL,
            "IRS": ModuleCode.IRS,
            "SYSTEM": ModuleCode.SYSTEM,
        },
        "descriptions": {
            "permission_levels": {
                PermissionLevel.NONE: "No access",
                PermissionLevel.ENQUIRY: "View only",
                PermissionLevel.OPERATOR: "Add/Edit",
                PermissionLevel.SUPERVISOR: "Add/Edit/Delete",
                PermissionLevel.MANAGER: "Full access including period close",
                PermissionLevel.ADMIN: "System administration",
            },
            "modules": {
                ModuleCode.SALES: "Sales Ledger",
                ModuleCode.PURCHASE: "Purchase Ledger",
                ModuleCode.STOCK: "Stock Control",
                ModuleCode.GENERAL: "General Ledger",
                ModuleCode.IRS: "IRS System",
                ModuleCode.SYSTEM: "System Administration",
            }
        }
    }


@router.post("/initialize/admin")
def initialize_admin_user(
    db: Session = Depends(get_db)
):
    """Initialize default admin user (for setup only)"""
    
    service = UserService(db)
    
    # Check if any users exist
    existing_users = service.list_users(limit=1)
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users already exist. Cannot initialize admin."
        )
    
    admin_user = service.create_default_admin()
    
    return {
        "message": "Default admin user created",
        "username": admin_user.username,
        "password": "admin123",
        "warning": "Please change the default password immediately"
    }