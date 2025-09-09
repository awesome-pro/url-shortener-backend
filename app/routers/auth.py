from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.schemas.user import (
    UserCreate, UserListResponse, UserLogin, UserResponse,
    GoogleOAuthRequest, GoogleOAuthCallback, GoogleOAuthURL
)
from app.services.auth import AuthService
from app.services.google_oauth import GoogleOAuthService
from app.core.deps import get_current_active_user
from app.core.config import settings
from app.core.cookies import set_auth_cookie, clear_auth_cookie
from app.models.user import User
from app.core.pagination_deps import PaginationDep

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
    set_auth_cookie(response, access_token)
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
    set_auth_cookie(response, access_token)
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
    clear_auth_cookie(response)
    return {"message": "Successfully logged out"}


@router.get("/users", response_model=UserListResponse)
async def get_users(
    pagination: PaginationDep,
    db: AsyncSession = Depends(get_db_session)
):
    """Get all users."""
    return await AuthService.get_users(db, pagination)


# Google OAuth endpoints
@router.get("/google/url", response_model=GoogleOAuthURL)
async def get_google_oauth_url():
    """Get Google OAuth authorization URL."""
    auth_url = await GoogleOAuthService.get_google_oauth_url()
    return GoogleOAuthURL(auth_url=auth_url)


@router.post("/google/callback", response_model=UserResponse)
async def google_oauth_callback(
    callback_data: GoogleOAuthCallback,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    """Handle Google OAuth callback with authorization code."""
    try:
        # Exchange code for tokens
        tokens = await GoogleOAuthService.exchange_code_for_tokens(callback_data.code)
        
        # Get user info using access token
        google_user_info = await GoogleOAuthService.get_google_user_info(tokens['access_token'])
        
        # Add Google ID to user info
        google_user_info['google_id'] = google_user_info['id']
        
        # Find or create user
        user = await GoogleOAuthService.find_or_create_oauth_user(db, google_user_info)
        
        # Create JWT token
        access_token = AuthService.create_user_token(user)
        
        # Set cookie with proper cross-domain configuration
        set_auth_cookie(response, access_token)
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.post("/google/verify", response_model=UserResponse)
async def google_oauth_verify(
    oauth_request: GoogleOAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    """Verify Google ID token and authenticate user."""
    try:
        # Verify ID token
        google_user_info = await GoogleOAuthService.verify_google_token(oauth_request.id_token)
        
        # Find or create user
        user = await GoogleOAuthService.find_or_create_oauth_user(db, google_user_info)
        
        # Create JWT token
        access_token = AuthService.create_user_token(user)
        
        # Set cookie with proper cross-domain configuration
        set_auth_cookie(response, access_token)
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )