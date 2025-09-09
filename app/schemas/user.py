from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

from app.models.user import UserRole, UserStatus
from app.utils.pagination import PaginatedResponse


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

class UserResponse(UserBase):
    id: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
    
class UserListResponse(PaginatedResponse[UserResponse]):
    pass


class UserProfile(UserResponse):
    updated_at: datetime
    total_urls: Optional[int] = 0
    total_clicks: Optional[int] = 0


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
