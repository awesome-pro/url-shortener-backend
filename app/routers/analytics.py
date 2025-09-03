from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.services.analytics import AnalyticsService
from app.core.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get dashboard statistics for the current user."""
    stats = await AnalyticsService.get_user_dashboard_stats(db, current_user)
    return stats
