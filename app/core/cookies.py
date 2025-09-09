from fastapi import Response
from app.core.config import settings


def set_auth_cookie(response: Response, token: str) -> None:
    """Set authentication cookie with proper cross-domain configuration"""
    
    # Determine cookie settings based on environment
    if settings.debug:
        # Local development settings
        response.set_cookie(
            key="access_token",
            value=token,
            max_age=settings.jwt_access_token_expire_minutes * 60,
            httponly=True,
            secure=False,  # HTTP in development
            samesite="lax",
            # domain=settings.cookie_domain
        )
    else:
        # Production settings for cross-subdomain
        response.set_cookie(
            key="access_token",
            value=token,
            max_age=settings.jwt_access_token_expire_minutes * 60,
            httponly=True,
            secure=True,  # HTTPS required
            samesite="none",  # Required for cross-site requests
            domain=settings.cookie_domain
        )


def clear_auth_cookie(response: Response) -> None:
    """Clear authentication cookie with proper cross-domain configuration"""
    
    if settings.debug:
        # Local development
        response.delete_cookie("access_token")
    else:
        # Production - must match the domain used when setting
        response.delete_cookie(
            "access_token",
            domain=settings.cookie_domain,
            secure=True,
            samesite="none"
        )
