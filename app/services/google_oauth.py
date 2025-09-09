from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import Dict, Any
import httpx
import uuid

from app.core.config import settings
from app.models.user import User, UserStatus


class GoogleOAuthService:
    """Service for handling Google OAuth authentication"""
    
    @staticmethod
    async def verify_google_token(token: str) -> Dict[str, Any]:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                settings.google_client_id
            )
            
            # Additional validation
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
            if idinfo['aud'] != settings.google_client_id:
                raise ValueError('Wrong audience.')
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token verification failed: {str(e)}"
            )
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Google using access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to fetch user info from Google"
                    )
                print("response: ", response.json())
                return response.json()
                
        except httpx.HTTPError as e:
            print("error: ", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Google: {str(e)}"
            )
        except Exception as e:
            print("error: ", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Google: {str(e)}"
            )
    
    @staticmethod
    async def find_or_create_oauth_user(
        db: AsyncSession, 
        google_user_info: Dict[str, Any]
    ) -> User:
        """Find existing user or create new OAuth user"""
        
        google_id = google_user_info['google_id']
        email = google_user_info['email']
        name = google_user_info.get('name', '')
        picture = google_user_info.get('picture', '')
        
        # First, try to find user by Google ID
        result = await db.execute(
            select(User).where(User.google_id == google_id)
        )
        existing_user = result.scalars().first()
        
        if existing_user:
            # Update user info if needed
            if existing_user.avatar_url != picture:
                existing_user.avatar_url = picture
                await db.commit()
                await db.refresh(existing_user)
            return existing_user
        
        # Check if user exists with same email (regular user wanting to link Google)
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_email_user = result.scalars().first()
        
        if existing_email_user and not existing_email_user.is_oauth_user:
            # Link Google account to existing user
            existing_email_user.google_id = google_id
            existing_email_user.avatar_url = picture
            existing_email_user.is_oauth_user = True
            await db.commit()
            await db.refresh(existing_email_user)
            return existing_email_user
        
        if existing_email_user and existing_email_user.is_oauth_user:
            # OAuth user exists but different Google ID - this shouldn't happen
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists"
            )
        
        # Create new OAuth user
        username = GoogleOAuthService._generate_unique_username(name, email)
        
        # Check if username already exists and make it unique
        counter = 1
        original_username = username
        while True:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            if not result.scalars().first():
                break
            username = f"{original_username}{counter}"
            counter += 1
        
        new_user = User(
            id=uuid.uuid4().hex,
            email=email,
            username=username,
            google_id=google_id,
            avatar_url=picture,
            is_oauth_user=True,
            status=UserStatus.ACTIVE,
            hashed_password=None  # OAuth users don't have passwords
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def _generate_unique_username(name: str, email: str) -> str:
        """Generate a unique username from name or email"""
        if name:
            # Clean the name: remove special characters, convert to lowercase
            username = ''.join(c.lower() for c in name if c.isalnum())
            if len(username) >= 3:
                return username[:20]  # Limit to 20 characters
        
        # Fallback to email prefix
        email_prefix = email.split('@')[0]
        username = ''.join(c.lower() for c in email_prefix if c.isalnum())
        return username[:20] if username else f"user{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    async def get_google_oauth_url() -> str:
        """Generate Google OAuth authorization URL"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"{base_url}?{query_string}"
    
    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": settings.google_redirect_uri,
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to exchange code for tokens"
                    )
                
                return response.json()
                
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Google: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token exchange failed: {str(e)}"
            )

