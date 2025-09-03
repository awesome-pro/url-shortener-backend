from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.connection import get_db_session
from app.schemas.url import URLCreate, URLUpdate, URLResponse, URLListResponse
from app.services.url_shortener import URLShortenerService
from app.services.analytics import AnalyticsService
from app.core.deps import get_current_active_user
from app.models.user import User
from app.core.config import settings
import math

router = APIRouter(prefix="/urls", tags=["URLs"])


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    url_data: URLCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new shortened URL."""
    url = await URLShortenerService.create_short_url(db, url_data, current_user)
    
    # Add the full short URL to response
    url_dict = {
        "id": url.id,
        "original_url": url.original_url,
        "short_code": url.short_code,
        "title": url.title,
        "description": url.description,
        "is_active": url.is_active,
        "click_count": url.click_count,
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "expires_at": url.expires_at,
        "short_url": f"{settings.base_url}/{url.short_code}"
    }
    
    return url_dict


@router.get("/", response_model=URLListResponse)
async def get_user_urls(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's URLs with pagination."""
    skip = (page - 1) * per_page
    urls, total = await URLShortenerService.get_user_urls(db, current_user, skip, per_page)
    
    # Add short_url to each URL
    urls_with_short_url = []
    for url in urls:
        url_dict = {
            "id": url.id,
            "original_url": url.original_url,
            "short_code": url.short_code,
            "title": url.title,
            "description": url.description,
            "is_active": url.is_active,
            "click_count": url.click_count,
            "created_at": url.created_at,
            "updated_at": url.updated_at,
            "expires_at": url.expires_at,
            "short_url": f"{settings.base_url}/{url.short_code}"
        }
        urls_with_short_url.append(url_dict)
    
    pages = math.ceil(total / per_page)
    
    return {
        "urls": urls_with_short_url,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages
    }


@router.get("/{url_id}", response_model=URLResponse)
async def get_url(
    url_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific URL."""
    from sqlalchemy import select, and_
    from app.models.url import URL
    
    result = await db.execute(
        select(URL).where(
            and_(URL.id == url_id, URL.owner_id == current_user.id)
        )
    )
    url = result.scalars().first()
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    
    url_dict = {
        "id": url.id,
        "original_url": url.original_url,
        "short_code": url.short_code,
        "title": url.title,
        "description": url.description,
        "is_active": url.is_active,
        "click_count": url.click_count,
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "expires_at": url.expires_at,
        "short_url": f"{settings.base_url}/{url.short_code}"
    }
    
    return url_dict


@router.put("/{url_id}", response_model=URLResponse)
async def update_url(
    url_id: int,
    url_update: URLUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update a URL."""
    url = await URLShortenerService.update_url(db, url_id, current_user, url_update)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    
    url_dict = {
        "id": url.id,
        "original_url": url.original_url,
        "short_code": url.short_code,
        "title": url.title,
        "description": url.description,
        "is_active": url.is_active,
        "click_count": url.click_count,
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "expires_at": url.expires_at,
        "short_url": f"{settings.base_url}/{url.short_code}"
    }
    
    return url_dict


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    url_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a URL."""
    success = await URLShortenerService.delete_url(db, url_id, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )


@router.get("/{url_id}/analytics")
async def get_url_analytics(
    url_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get analytics for a specific URL."""
    analytics = await AnalyticsService.get_url_analytics(db, url_id, current_user)
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    
    return analytics


@router.get("/{url_id}/analytics/daily")
async def get_url_daily_analytics(
    url_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get daily analytics for a specific URL."""
    daily_clicks = await AnalyticsService.get_daily_clicks(db, url_id, current_user, days)
    return {"daily_clicks": daily_clicks}


@router.get("/{url_id}/analytics/referrers")
async def get_url_referrers(
    url_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get top referrers for a specific URL."""
    referrers = await AnalyticsService.get_top_referrers(db, url_id, current_user, limit)
    return {"referrers": referrers}
