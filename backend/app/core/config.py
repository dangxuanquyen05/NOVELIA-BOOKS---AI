"""Core application settings management via Pydantic Settings."""

import json
from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Application settings schema reading from environment variables and .env file."""

    PROJECT_NAME: str = "NOVELIA BOOKS API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database Configuration (MySQL Server)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "novelia_books"

    # JWT & Authentication Security
    JWT_SECRET: str = "novelia-books-dev-super-secret-key-change-in-production-min32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days

    # CORS Origins (default: Vite development dev-server)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Shipping Carrier Integrations (GHN & GHTK)
    SHIPPING_ENVIRONMENT: str = "sandbox"  # 'mock', 'sandbox', 'live'
    DEFAULT_SHIPPING_CARRIER: str = "GHN"
    
    # GHN (Giao Hàng Nhanh)
    GHN_API_URL: str = "https://dev-online-gateway.ghn.vn/shiip/public-api/v2"
    GHN_TOKEN: str = ""
    GHN_SHOP_ID: int = 0
    GHN_CLIENT_PHONE: str = "0987654321"
    GHN_WEBHOOK_SECRET: str = "novelia-ghn-webhook-secret"

    # GHTK (Giao Hàng Tiết Kiệm)
    GHTK_API_URL: str = "https://services-staging.ghtklab.com/services/shipment"
    GHTK_TOKEN: str = ""
    GHTK_WEBHOOK_SECRET: str = "novelia-ghtk-webhook-secret"

    # AI Assistant & Tool Execution (Phase 9)
    AI_PROVIDER: str = "mock"  # 'mock', 'gemini', 'openai'
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT_SECONDS: int = 20
    AI_RATE_LIMIT_PER_MINUTE: int = 20

    # Email & Notifications (Phase 12)
    EMAIL_PROVIDER: str = "mock"  # 'mock', 'smtp'
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@novelia.vn"
    SMTP_FROM_NAME: str = "NOVELIA BOOKS"
    SMTP_TIMEOUT_SECONDS: int = 5

    # Smart Address & Map/Geocoding Integration (VietMap / Mock)
    GEOCODING_PROVIDER: str = "auto"  # 'auto', 'vietmap', 'mock'
    VIETMAP_API_KEY: str = ""
    VIETMAP_API_URL: str = "https://maps.vietmap.vn/api"


    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Normalize CORS origins from JSON string or comma-separated string."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.strip("[]").split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173"]

    @property
    def database_url(self) -> URL:
        """Construct secure SQLAlchemy URL object handling special password characters."""
        return URL.create(
            drivername="mysql+pymysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD if self.DB_PASSWORD else None,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={"charset": "utf8mb4"},
        )

    @property
    def masked_database_url(self) -> str:
        """Return database connection string with password safely masked for logging."""
        pwd_display = "***" if self.DB_PASSWORD else ""
        user_part = f"{self.DB_USER}:{pwd_display}@" if self.DB_USER else ""
        return f"mysql+pymysql://{user_part}{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
