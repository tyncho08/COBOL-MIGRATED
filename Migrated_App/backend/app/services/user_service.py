"""
User Management Service
Handles user account management, permissions, and system administration
Migrated from ACAS user management modules
"""
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.system import User, AuditTrail
from app.config.security import (
    get_password_hash, 
    verify_password,
    PermissionLevel,
    ModuleCode
)
from app.schemas.auth import UserResponse
from app.core.audit.audit_service import AuditService


class UserService:
    """
    User management service implementing ACAS user administration logic
    Handles user creation, permission management, and security features
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)
    
    def create_user(
        self,
        username: str,
        full_name: str,
        email: str,
        password: str,
        user_level: int = 1,
        module_access: Optional[Dict[str, int]] = None,
        is_superuser: bool = False,
        allowed_companies: Optional[List[str]] = None,
        created_by_user_id: int = None
    ) -> User:
        """Create new user account"""
        
        # Validate username uniqueness
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{username}' already exists"
            )
        
        # Validate email uniqueness
        existing_email = self.db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{email}' already exists"
            )
        
        # Set default module access if not provided
        if module_access is None:
            module_access = {
                ModuleCode.SALES: PermissionLevel.ENQUIRY,
                ModuleCode.PURCHASE: PermissionLevel.ENQUIRY,
                ModuleCode.STOCK: PermissionLevel.ENQUIRY,
                ModuleCode.GENERAL: PermissionLevel.ENQUIRY,
                ModuleCode.SYSTEM: PermissionLevel.NONE,
            }
        
        # Create user
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            hashed_password=get_password_hash(password),
            user_level=user_level,
            module_access=module_access,
            is_superuser=is_superuser,
            allowed_companies=allowed_companies or [],
            is_active=True,
            login_count=0,
            created_at=datetime.now()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Audit trail
        if created_by_user_id:
            self.audit.log_transaction(
                table_name="users",
                record_id=user.id,
                operation="CREATE",
                user_id=created_by_user_id,
                details=f"User {username} created"
            )
        
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """List users with filtering"""
        query = self.db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        return query.order_by(User.username).offset(skip).limit(limit).all()
    
    def update_user(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        user_level: Optional[int] = None,
        module_access: Optional[Dict[str, int]] = None,
        is_superuser: Optional[bool] = None,
        allowed_companies: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        updated_by_user_id: int = None
    ) -> User:
        """Update user account"""
        
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Store old values for audit
        old_values = {
            "full_name": user.full_name,
            "email": user.email,
            "user_level": user.user_level,
            "module_access": user.module_access,
            "is_superuser": user.is_superuser,
            "allowed_companies": user.allowed_companies,
            "is_active": user.is_active,
        }
        
        # Check email uniqueness if changing
        if email and email != user.email:
            existing_email = self.db.query(User).filter(
                and_(User.email == email, User.id != user_id)
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{email}' already exists"
                )
        
        # Update fields
        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            user.email = email
        if user_level is not None:
            user.user_level = user_level
        if module_access is not None:
            user.module_access = module_access
        if is_superuser is not None:
            user.is_superuser = is_superuser
        if allowed_companies is not None:
            user.allowed_companies = allowed_companies
        if is_active is not None:
            user.is_active = is_active
        
        user.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        if updated_by_user_id:
            changes = []
            for field, old_value in old_values.items():
                new_value = getattr(user, field)
                if old_value != new_value:
                    changes.append(f"{field}: {old_value} -> {new_value}")
            
            if changes:
                self.audit.log_transaction(
                    table_name="users",
                    record_id=user.id,
                    operation="UPDATE",
                    user_id=updated_by_user_id,
                    details=f"User {user.username} updated: {', '.join(changes)}"
                )
        
        return user
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        changed_by_user_id: int = None
    ) -> bool:
        """Change user password"""
        
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password (unless admin is changing it)
        if changed_by_user_id != user_id:
            # Admin changing password - no current password verification needed
            pass
        else:
            # User changing their own password
            if not verify_password(current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        if changed_by_user_id:
            self.audit.log_transaction(
                table_name="users",
                record_id=user.id,
                operation="PASSWORD_CHANGE",
                user_id=changed_by_user_id,
                details=f"Password changed for user {user.username}"
            )
        
        return True
    
    def deactivate_user(self, user_id: int, deactivated_by_user_id: int) -> User:
        """Deactivate user account"""
        
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        user.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="users",
            record_id=user.id,
            operation="DEACTIVATE",
            user_id=deactivated_by_user_id,
            details=f"User {user.username} deactivated"
        )
        
        return user
    
    def activate_user(self, user_id: int, activated_by_user_id: int) -> User:
        """Activate user account"""
        
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        user.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        self.audit.log_transaction(
            table_name="users",
            record_id=user.id,
            operation="ACTIVATE",
            user_id=activated_by_user_id,
            details=f"User {user.username} activated"
        )
        
        return user
    
    def update_user_permissions(
        self,
        user_id: int,
        module_access: Dict[str, int],
        updated_by_user_id: int
    ) -> User:
        """Update user module permissions"""
        
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        old_permissions = user.module_access.copy() if user.module_access else {}
        user.module_access = module_access
        user.updated_at = datetime.now()
        
        self.db.commit()
        
        # Audit trail
        changes = []
        for module, level in module_access.items():
            old_level = old_permissions.get(module, 0)
            if old_level != level:
                changes.append(f"{module}: {old_level} -> {level}")
        
        if changes:
            self.audit.log_transaction(
                table_name="users",
                record_id=user.id,
                operation="PERMISSIONS_UPDATE",
                user_id=updated_by_user_id,
                details=f"Permissions updated for {user.username}: {', '.join(changes)}"
            )
        
        return user
    
    def get_user_statistics(self, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Dict:
        """Get user statistics"""
        
        query = self.db.query(User)
        
        if from_date:
            query = query.filter(User.created_at >= from_date)
        if to_date:
            query = query.filter(User.created_at <= to_date)
        
        total_users = query.count()
        active_users = query.filter(User.is_active == True).count()
        inactive_users = total_users - active_users
        superusers = query.filter(User.is_superuser == True).count()
        
        # Login statistics
        recent_logins = self.db.query(User).filter(
            User.last_login >= datetime.now() - timedelta(days=30),
            User.is_active == True
        ).count()
        
        # Permission level distribution
        permission_stats = {}
        users_with_permissions = query.filter(User.module_access.isnot(None)).all()
        
        for user in users_with_permissions:
            for module, level in (user.module_access or {}).items():
                if module not in permission_stats:
                    permission_stats[module] = {}
                if level not in permission_stats[module]:
                    permission_stats[module][level] = 0
                permission_stats[module][level] += 1
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "superusers": superusers,
            "recent_logins": recent_logins,
            "permission_distribution": permission_stats
        }
    
    def get_user_activity(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get user activity from audit trail"""
        
        since_date = datetime.now() - timedelta(days=days)
        
        activities = self.db.query(AuditTrail).filter(
            and_(
                AuditTrail.user_id == user_id,
                AuditTrail.timestamp >= since_date
            )
        ).order_by(AuditTrail.timestamp.desc()).limit(100).all()
        
        return [
            {
                "timestamp": activity.timestamp,
                "operation": activity.operation_type,
                "table": activity.table_name,
                "record_id": activity.record_id,
                "details": activity.details,
                "ip_address": activity.ip_address
            }
            for activity in activities
        ]
    
    def create_default_admin(self) -> User:
        """Create default admin user if none exists"""
        
        admin_exists = self.db.query(User).filter(User.is_superuser == True).first()
        if admin_exists:
            return admin_exists
        
        # Create default admin
        admin_user = User(
            username="admin",
            full_name="System Administrator",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True,
            is_active=True,
            user_level=9,
            module_access={
                ModuleCode.SALES: PermissionLevel.ADMIN,
                ModuleCode.PURCHASE: PermissionLevel.ADMIN,
                ModuleCode.STOCK: PermissionLevel.ADMIN,
                ModuleCode.GENERAL: PermissionLevel.ADMIN,
                ModuleCode.SYSTEM: PermissionLevel.ADMIN,
            },
            allowed_companies=[],
            login_count=0,
            created_at=datetime.now()
        )
        
        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)
        
        return admin_user