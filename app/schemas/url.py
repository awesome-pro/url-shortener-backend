from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, List

from app.models.url import URLStatus
from app.utils.pagination import PaginatedResponse


class URLBase(BaseModel):
    original_url: HttpUrl
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class URLCreate(URLBase):
    custom_code: Optional[str] = Field(None, min_length=3, max_length=10, pattern="^[a-zA-Z0-9_-]+$")
    expires_at: Optional[datetime] = None


class URLUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[URLStatus] = None
    expires_at: Optional[datetime] = None


class URLResponse(URLBase):
    id: str
    short_code: str
    status: URLStatus
    click_count: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    short_url: str
    
    class Config:
        from_attributes = True


# Using the new generic pagination response
URLListResponse = PaginatedResponse[URLResponse]


class URLAnalytics(BaseModel):
    url_id: str
    short_code: str
    original_url: str
    total_clicks: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int
    created_at: datetime
    last_clicked: Optional[datetime] = None


class ClickAnalytics(BaseModel):
    date: str
    clicks: int


class URLDetailedAnalytics(URLAnalytics):
    daily_clicks: List[ClickAnalytics]
    top_referrers: List[dict]
    top_countries: List[dict]
