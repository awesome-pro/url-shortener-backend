from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserListResponse, UserLogin, UserProfile
from app.core.security import verify_password, get_password_hash, create_access_token
from typing import Optional

from app.core.pagination_deps import PaginationDep
from app.services.pagination_service import PaginationService
from app.utils.pagination import PaginatedResponse


class AuthService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        result = await db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        existing_user = result.scalars().first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> Optional[User]:
        """Authenticate user with email and password."""
        result = await db.execute(select(User).where(User.email == login_data.email))
        user = result.scalars().first()
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive or Suspended user"
            )
        
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_user_profile(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        return user
    
    @staticmethod
    def create_user_token(user: User) -> str:
        """Create access token for user."""
        return create_access_token(data={"sub": user.id, "email": user.email, "role": user.role.value})


    @staticmethod
    async def get_users(db: AsyncSession, pagination: PaginationDep) -> UserListResponse:
        """Get all users."""
        users = await db.execute(select(User).offset(pagination.skip).limit(pagination.limit))
        total = await db.execute(select(func.count()).select_from(User))
        return PaginatedResponse.create(data=users.scalars().all(), page=pagination.page, limit=pagination.limit, total=total.scalar())