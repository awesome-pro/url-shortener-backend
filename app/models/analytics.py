from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import uuid


class URLClick(Base):
    __tablename__ = "url_clicks"

    id = Column(String(255), primary_key=True, index=True, default=uuid.uuid4().hex)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Foreign Key
    url_id = Column(String(255), ForeignKey("urls.id"), nullable=False)
    
    # Relationship
    url = relationship("URL", back_populates="clicks")
