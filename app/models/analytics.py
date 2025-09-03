from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class URLClick(Base):
    __tablename__ = "url_clicks"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Foreign Key
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    
    # Relationship
    url = relationship("URL", back_populates="clicks")
