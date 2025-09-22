"""
Authentication Schemas
Pydantic models for authentication and authorization
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """User information response"""
    id: int
    username: str
    full_name: str
    email: str
    is_active: bool
    is_superuser: bool
    user_level: int
    module_access: Dict[str, int]
    allowed_companies: list = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class PasswordReset(BaseModel):
    """Password reset request"""
    email: str
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str