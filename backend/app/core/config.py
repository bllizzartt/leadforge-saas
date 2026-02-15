from typing import Any
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "LeadForge"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/leadforge"
    SYNC_DATABASE_URL: str = "postgresql://user:password@localhost:5432/leadforge"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days for refresh
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External APIs (get free tiers)
    CLEARBIT_KEY: str = ""
    HUNTER_KEY: str = ""
    NEVERBOUNCE_KEY: str = ""
    BUILTWITH_KEY: str = ""
    
    # Scraping
    LINKEDIN_COOKIE: str = ""
    PROXY_URL: str = ""
    
    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
