import string
import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.models.url import URL, URLStatus
from app.models.user import User
from app.schemas.url import URLCreate, URLUpdate
from app.core.config import settings
from app.database.connection import get_redis_client
import json


class URLShortenerService:
    @staticmethod
    def generate_short_code(length: int = None) -> str:
        """Generate a random short code."""
        if length is None:
            length = settings.short_code_length
        
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    async def is_short_code_available(db: AsyncSession, short_code: str) -> bool:
        """Check if short code is available."""
        result = await db.execute(select(URL).where(URL.short_code == short_code))
        return result.scalars().first() is None
    
    @staticmethod
    async def generate_unique_short_code(db: AsyncSession, length: int = None) -> str:
        """Generate a unique short code."""
        for _ in range(settings.max_retries_for_unique_code):
            short_code = URLShortenerService.generate_short_code(length)
            if await URLShortenerService.is_short_code_available(db, short_code):
                return short_code
        
        # If we couldn't generate a unique code, increase length and try again
        return await URLShortenerService.generate_unique_short_code(
            db, (length or settings.short_code_length) + 1
        )
    
    @staticmethod
    async def create_short_url(
        db: AsyncSession, 
        url_data: URLCreate, 
        user: User
    ) -> URL:
        """Create a new shortened URL."""
        # Validate custom code if provided
        if url_data.custom_code:
            if not await URLShortenerService.is_short_code_available(db, url_data.custom_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom short code already exists"
                )
            short_code = url_data.custom_code
        else:
            short_code = await URLShortenerService.generate_unique_short_code(db)
        
        # Create URL record
        db_url = URL(
            original_url=str(url_data.original_url),
            short_code=short_code,
            title=url_data.title,
            description=url_data.description,
            expires_at=url_data.expires_at,
            owner_id=user.id
        )
        
        db.add(db_url)
        await db.commit()
        await db.refresh(db_url)
        
        # Cache the URL for faster redirects
        await URLShortenerService.cache_url(db_url)
        
        return db_url
    
    @staticmethod
    async def get_url_by_short_code(
        db: AsyncSession, 
        short_code: str,
        check_expiry: bool = True
    ) -> Optional[URL]:
        """Get URL by short code."""
        # Try to get from cache first
        redis_client = await get_redis_client()
        cached_data = await redis_client.get(f"url:{short_code}")
        
        if cached_data:
            url_data = json.loads(cached_data)
            # Check if expired
            if check_expiry and url_data.get('expires_at'):
                expires_at = datetime.fromisoformat(url_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    await redis_client.delete(f"url:{short_code}")
                    return None
            
            # Check if active
            if url_data.get('status') == URLStatus.ACTIVE.value:
                # Create a minimal URL object for redirect
                url = URL()
                url.id = url_data['id']
                url.original_url = url_data['original_url']
                url.status = URLStatus(url_data['status'])
                url.expires_at = datetime.fromisoformat(url_data['expires_at']) if url_data['expires_at'] else None
                url.owner_id = url_data['owner_id']
                url.short_code = short_code
                return url
        
        # Get from database
        result = await db.execute(
            select(URL).where(
                and_(
                    URL.short_code == short_code,
                    URL.status == URLStatus.ACTIVE
                )
            )
        )
        url = result.scalars().first()
        
        if url and check_expiry and url.expires_at:
            if datetime.utcnow() > url.expires_at:
                return None
        
        return url
    
    @staticmethod
    async def get_user_urls(
        db: AsyncSession,
        user: User,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[URL], int]:
        """Get user's URLs with pagination."""
        # Get total count
        count_result = await db.execute(
            select(func.count(URL.id)).where(URL.owner_id == user.id)
        )
        total = count_result.scalar()
        
        # Get URLs
        result = await db.execute(
            select(URL)
            .where(URL.owner_id == user.id)
            .order_by(URL.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        urls = result.scalars().all()
        
        return urls, total
    
    @staticmethod
    async def update_url(
        db: AsyncSession,
        url_id: str,
        user: User,
        url_update: URLUpdate
    ) -> Optional[URL]:
        """Update a URL."""
        result = await db.execute(
            select(URL).where(
                and_(URL.id == url_id, URL.owner_id == user.id)
            )
        )
        url = result.scalars().first()
        
        if not url:
            return None
        
        # Update fields
        update_data = url_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(url, field, value)
        
        await db.commit()
        await db.refresh(url)
        
        # Update cache
        await URLShortenerService.cache_url(url)
        
        return url
    
    @staticmethod
    async def delete_url(
        db: AsyncSession,
        url_id: str,
        user: User
    ) -> bool:
        """Delete a URL."""
        result = await db.execute(
            select(URL).where(
                and_(URL.id == url_id, URL.owner_id == user.id)
            )
        )
        url = result.scalars().first()
        
        if not url:
            return False
        
        # Remove from cache
        redis_client = await get_redis_client()
        await redis_client.delete(f"url:{url.short_code}")
        
        # Delete from database
        await db.delete(url)
        await db.commit()
        
        return True
    
    @staticmethod
    async def cache_url(url: URL):
        """Cache URL data in Redis."""
        redis_client = await get_redis_client()
        
        url_data = {
            "id": url.id,
            "original_url": url.original_url,
            "status": url.status.value,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
            "owner_id": url.owner_id
        }
        
        await redis_client.setex(
            f"url:{url.short_code}",
            settings.cache_ttl,
            json.dumps(url_data)
        )
