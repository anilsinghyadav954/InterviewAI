from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
from pathlib import Path

# Locate .env file relative to current file or backend directory
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "interview_ai"
    JWT_SECRET_KEY: str = "default_insecure_secret_key_please_change_via_env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    ENVIRONMENT: str = "production"
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP Email Delivery Configuration (Gmail / standard SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_USER: str = ""  # backwards compatibility alias
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "InterviewAI"
    SMTP_USE_TLS: bool = True

    @property
    def effective_smtp_username(self) -> str:
        return (self.SMTP_USERNAME or self.SMTP_USER or "").strip()

    @property
    def effective_smtp_from_email(self) -> str:
        return (self.SMTP_FROM_EMAIL or self.effective_smtp_username or "noreply@interviewai.com").strip()

    @property
    def is_smtp_configured(self) -> bool:
        """
        Returns True when valid, non-placeholder SMTP credentials are configured.
        Falls back to safe development simulation if host/username/password are missing or placeholders.
        """
        host = (self.SMTP_HOST or "").strip()
        user = self.effective_smtp_username
        pwd = (self.SMTP_PASSWORD or "").strip()

        if not (host and user and pwd):
            return False

        # Exclude common placeholder markers
        placeholders = ["<", ">", "your_email", "example.com", "your-app-password", "your_16_character_app_password"]
        if any(p in user.lower() for p in placeholders) or any(p in pwd.lower() for p in placeholders):
            return False

        return True

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
