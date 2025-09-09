from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import AuthService
from app.core.deps import get_current_active_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new user."""
    user = await AuthService.create_user(db, user_data)
    access_token = AuthService.create_user_token(user)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        secure=not settings.debug,
        samesite="lax"
    )
    return user


@router.post("/sign-in", response_model=UserResponse)
async def login(
    login_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    """Login user and set access token in cookie."""
    user = await AuthService.authenticate_user(db, login_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = AuthService.create_user_token(user)
    
    # Set cookie with proper security settings
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,  # Convert to seconds
        httponly=True,  # Prevent XSS attacks
        secure=not settings.debug,  # Use secure in production
        samesite="lax"  # CSRF protection
    )
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user = Depends(get_current_active_user)
):
    """Get current user profile."""
    return current_user

@router.post("/sign-out", status_code=status.HTTP_200_OK)
async def sign_out(
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """Sign out user and clear access token."""
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}
