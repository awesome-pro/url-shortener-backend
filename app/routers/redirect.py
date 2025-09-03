from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.services.url_shortener import URLShortenerService
from app.services.analytics import AnalyticsService

router = APIRouter(tags=["Redirect"])


@router.get("/{short_code}")
async def redirect_to_original_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Redirect to the original URL and track analytics."""
    # Get URL from database/cache
    url = await URLShortenerService.get_url_by_short_code(db, short_code)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found or expired"
        )
    
    # Extract client information for analytics
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")
    
    # Record the click (async, non-blocking)
    await AnalyticsService.record_click(
        db, url, client_ip, user_agent, referer
    )
    
    # Redirect to original URL
    return RedirectResponse(url=url.original_url, status_code=status.HTTP_302_FOUND)
