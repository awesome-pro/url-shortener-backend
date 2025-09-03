from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.core.security import verify_token
from app.services.auth import AuthService
from app.models.user import User, UserStatus
from typing import Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = await AuthService.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_optional_current_user(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not authorization:
        return None
    
    try:
        from fastapi.security.utils import get_authorization_scheme_param
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        
        payload = verify_token(token)
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = await AuthService.get_user_by_email(db, email=email)
        return user
    except Exception:
        return None
