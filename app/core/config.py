from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="postgresql+asyncpg://postgres:Abhi123@localhost:5432/fast", env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # JWT
    jwt_secret_key: str = Field(default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=24*60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Application
    app_name: str = Field(default="URL Shortener", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    base_url: str = Field(default="http://localhost:8080", env="BASE_URL")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "https://shortenurl.abhinandan.pro", "https://shorturl.abhinandan.pro"], 
        env="ALLOWED_ORIGINS"
    )
    
    # Cookie settings for cross-domain
    cookie_domain: str = Field(default=".abhinandan.pro", env="COOKIE_DOMAIN")  # Leading dot for subdomain sharing
    frontend_url: str = Field(default="https://shortenurl.abhinandan.pro", env="FRONTEND_URL")
    
    # Short URL Configuration
    short_code_length: int = Field(default=6, env="SHORT_CODE_LENGTH")
    max_retries_for_unique_code: int = Field(default=5, env="MAX_RETRIES_FOR_UNIQUE_CODE")
    
    # Analytics
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Google OAuth
    google_client_id: str = Field(default="", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="https://shortenurl.abhinandan.pro/auth/callback/google", env="GOOGLE_REDIRECT_URI")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
