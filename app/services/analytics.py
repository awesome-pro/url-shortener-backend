from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models.url import URL, URLStatus
from app.models.analytics import URLClick
from app.models.user import User
from app.database.connection import get_redis_client
import json
import asyncio


class AnalyticsService:
    @staticmethod
    async def record_click(
        db: AsyncSession,
        url: URL,
        ip_address: str,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None
    ):
        """Record a click on a URL with minimal latency impact."""
        # Increment click count in database asynchronously
        asyncio.create_task(
            AnalyticsService._increment_click_count_db(db, url.id)
        )
        
        # Store detailed click data asynchronously
        asyncio.create_task(
            AnalyticsService._store_click_details(
                db, url.id, ip_address, user_agent, referer
            )
        )
        
        # Update Redis cache immediately for real-time stats
        await AnalyticsService._increment_click_count_cache(url.short_code)
    
    @staticmethod
    async def _increment_click_count_db(db: AsyncSession, url_id: str):
        """Increment click count in database (async)."""
        try:
            # Create a new session for this async operation
            from app.database.connection import async_session_maker
            async with async_session_maker() as session:
                result = await session.execute(select(URL).where(URL.id == url_id))
                url = result.scalars().first()
                if url:
                    url.click_count += 1
                    await session.commit()
        except Exception as e:
            # Log error but don't fail the redirect
            print(f"Error incrementing click count: {e}")
    
    @staticmethod
    async def _store_click_details(
        db: AsyncSession,
        url_id: str,
        ip_address: str,
        user_agent: Optional[str],
        referer: Optional[str]
    ):
        """Store detailed click information (async)."""
        try:
            # Create a new session for this async operation
            from app.database.connection import async_session_maker
            async with async_session_maker() as session:
                click = URLClick(
                    url_id=url_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    referer=referer
                )
                session.add(click)
                await session.commit()
        except Exception as e:
            # Log error but don't fail the redirect
            print(f"Error storing click details: {e}")
    
    @staticmethod
    async def _increment_click_count_cache(short_code: str):
        """Increment click count in Redis cache."""
        try:
            redis_client = await get_redis_client()
            
            # Increment daily counter
            today = datetime.utcnow().strftime("%Y-%m-%d")
            await redis_client.incr(f"clicks:{short_code}:{today}")
            await redis_client.expire(f"clicks:{short_code}:{today}", 86400 * 7)  # 7 days
            
            # Increment total counter
            await redis_client.incr(f"clicks:total:{short_code}")
            await redis_client.expire(f"clicks:total:{short_code}", 86400 * 30)  # 30 days
        except Exception as e:
            # Log error but don't fail the redirect
            print(f"Error updating click cache: {e}")
    
    @staticmethod
    async def get_url_analytics(
        db: AsyncSession,
        url_id: str,
        user: User
    ) -> Optional[Dict]:
        """Get analytics for a specific URL."""
        # Verify ownership
        result = await db.execute(
            select(URL).where(
                and_(URL.id == url_id, URL.owner_id == user.id)
            )
        )
        url = result.scalars().first()
        
        if not url:
            return None
        
        # Get click analytics
        now = datetime.utcnow()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Total clicks
        total_clicks = url.click_count
        
        # Clicks today
        clicks_today_result = await db.execute(
            select(func.count(URLClick.id)).where(
                and_(
                    URLClick.url_id == url_id,
                    func.date(URLClick.clicked_at) == today
                )
            )
        )
        clicks_today = clicks_today_result.scalar() or 0
        
        # Clicks this week
        clicks_week_result = await db.execute(
            select(func.count(URLClick.id)).where(
                and_(
                    URLClick.url_id == url_id,
                    func.date(URLClick.clicked_at) >= week_ago
                )
            )
        )
        clicks_this_week = clicks_week_result.scalar() or 0
        
        # Clicks this month
        clicks_month_result = await db.execute(
            select(func.count(URLClick.id)).where(
                and_(
                    URLClick.url_id == url_id,
                    func.date(URLClick.clicked_at) >= month_ago
                )
            )
        )
        clicks_this_month = clicks_month_result.scalar() or 0
        
        # Last clicked
        last_click_result = await db.execute(
            select(URLClick.clicked_at).where(URLClick.url_id == url_id)
            .order_by(desc(URLClick.clicked_at))
            .limit(1)
        )
        last_clicked = last_click_result.scalar()
        
        return {
            "url_id": url_id,
            "short_code": url.short_code,
            "original_url": url.original_url,
            "total_clicks": total_clicks,
            "clicks_today": clicks_today,
            "clicks_this_week": clicks_this_week,
            "clicks_this_month": clicks_this_month,
            "created_at": url.created_at,
            "last_clicked": last_clicked
        }
    
    @staticmethod
    async def get_daily_clicks(
        db: AsyncSession,
        url_id: str,
        user: User,
        days: int = 30
    ) -> List[Dict]:
        """Get daily click data for a URL."""
        # Verify ownership
        result = await db.execute(
            select(URL).where(
                and_(URL.id == url_id, URL.owner_id == user.id)
            )
        )
        url = result.scalars().first()
        
        if not url:
            return []
        
        # Get daily clicks for the last N days
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        result = await db.execute(
            select(
                func.date(URLClick.clicked_at).label('date'),
                func.count(URLClick.id).label('clicks')
            )
            .where(
                and_(
                    URLClick.url_id == url_id,
                    func.date(URLClick.clicked_at) >= start_date
                )
            )
            .group_by(func.date(URLClick.clicked_at))
            .order_by(func.date(URLClick.clicked_at))
        )
        
        daily_data = result.all()
        
        return [
            {
                "date": str(row.date),
                "clicks": row.clicks
            }
            for row in daily_data
        ]
    
    @staticmethod
    async def get_top_referrers(
        db: AsyncSession,
        url_id: str,
        user: User,
        limit: int = 10
    ) -> List[Dict]:
        """Get top referrers for a URL."""
        # Verify ownership
        result = await db.execute(
            select(URL).where(
                and_(URL.id == url_id, URL.owner_id == user.id)
            )
        )
        url = result.scalars().first()
        
        if not url:
            return []
        
        result = await db.execute(
            select(
                URLClick.referer,
                func.count(URLClick.id).label('count')
            )
            .where(
                and_(
                    URLClick.url_id == url_id,
                    URLClick.referer.isnot(None),
                    URLClick.referer != ''
                )
            )
            .group_by(URLClick.referer)
            .order_by(desc(func.count(URLClick.id)))
            .limit(limit)
        )
        
        referrers = result.all()
        
        return [
            {
                "referer": row.referer,
                "count": row.count
            }
            for row in referrers
        ]
    
    @staticmethod
    async def get_user_dashboard_stats(
        db: AsyncSession,
        user: User
    ) -> Dict:
        """Get dashboard statistics for a user."""
        # Total URLs
        total_urls_result = await db.execute(
            select(func.count(URL.id)).where(URL.owner_id == user.id)
        )
        total_urls = total_urls_result.scalar() or 0
        
        # Total clicks
        total_clicks_result = await db.execute(
            select(func.sum(URL.click_count)).where(URL.owner_id == user.id)
        )
        total_clicks = total_clicks_result.scalar() or 0
        
        # Active URLs
        active_urls_result = await db.execute(
            select(func.count(URL.id)).where(
                and_(URL.owner_id == user.id, URL.status == URLStatus.ACTIVE)
            )
        )
        active_urls = active_urls_result.scalar() or 0
        
        # Top performing URLs
        top_urls_result = await db.execute(
            select(URL.short_code, URL.original_url, URL.click_count)
            .where(URL.owner_id == user.id)
            .order_by(desc(URL.click_count))
            .limit(5)
        )
        top_urls = [
            {
                "short_code": row.short_code,
                "original_url": row.original_url,
                "clicks": row.click_count
            }
            for row in top_urls_result.all()
        ]
        
        return {
            "total_urls": total_urls,
            "total_clicks": total_clicks,
            "active_urls": active_urls,
            "top_urls": top_urls
        }
